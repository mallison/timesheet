import argparse
import datetime
import os
import re
from operator import itemgetter
from itertools import groupby

# TODO take list of files for summaries over longer than a week
# TODO could probably do the parsing with one cunning regexp (remember
# someone posted a perl prog to parse html with a regexp!)

DAYS = [datetime.date(2008, 9, d).strftime('%A') for d in range(1, 8)]
TASK_START_REGEXP = re.compile(r'^(\d{2})(\d{2})([ \w\/\.\-]*)$')
AFK = ['tea', 'lunch', 'afk']
ZERO = datetime.timedelta(0)


class TimeSheetError(Exception):
    """Base class for errors in the timesheet module."""
    pass


def parse(current_date, iterable):
    # parse the time slots into a list
    slots = []
    current_day = None
    for line in iterable:
        line = line.strip()
        m = TASK_START_REGEXP.match(line)
        if line in DAYS:
            # Record for a new days starts
            new_day = line
            if slots:
                # If this is not the first day we'll have a bogus
                # last slot created when then the clock out time
                # for the previous days was parsed. Delete it.
                del slots[-1]
                validate_previous_day(slots, current_day)
            validate_day(current_day, new_day)
            if current_day is not None:
                current_date += datetime.timedelta(days=1)
            current_day = new_day
        elif m:
            # Start of a new task
            hours, minutes = int(m.group(1)), int(m.group(2))
            task = m.group(3).strip()
            if not task:
                task = "misc"
            time = (current_date +
                    datetime.timedelta(hours=hours, minutes=minutes))
            if slots:
                validate_time(slots, task, time)
                if 'end' not in slots[-1]:
                    # Set the end time of the previous task to the
                    # start time of this one.
                    slots[-1]['end'] = time
            # Start a new slot
            slots.append({
                    'task': task,
                    'start': time,
                    'note': ''
                    })
        elif '-' * 20 in line:
            # Notes section at foot of file
            break
        elif slots:
            slots[-1]['note'] += line + '\n'
    # Remove the bogus slot created on parsing the clock out time
    # of the last day.
    del slots[-1]
    return slots


def validate_day(current_day, next_day):
    """
    Check ``next_day`` follows ``current_day`` or is Monday if
    ``current_day is None.

    >>> validate_day("Monday", "Tuesday")

    >>> validate_day("Monday", "Wednesday")
    Traceback (most recent call last):
    ...
    TimeSheetError: Wednesday does not follow Monday

    >>> validate_day(None, "Wednesday")
    Traceback (most recent call last):
    ...
    TimeSheetError: Week starts on Monday not Wednesday

    """
    if current_day is None and not next_day == DAYS[0]:
        raise TimeSheetError(
            "Week starts on %s not %s" % (DAYS[0], next_day))
    if current_day and not DAYS.index(current_day) == DAYS.index(next_day) - 1:
            raise TimeSheetError(
                "%s does not follow %s" % (next_day, current_day))


def validate_previous_day(slots, previous_day):
    """
    Check the last task of the previous day was closed.

    >>> slots = [
    ...    {'task': 'admin',
    ...     'start': datetime.datetime(2012, 2, 11, 12, 51)
    ...    }]
    >>> validate_previous_day(slots, "Tuesday")
    Traceback (most recent call last):
    ...
    TimeSheetError: No end time given for admin on Tuesday

    """
    if 'end' not in slots[-1]:
        raise TimeSheetError(
            "No end time given for %s on %s" %
            (slots[-1]['task'], previous_day))


def validate_time(slots, task, time):
    """
    Check new task starts after current task.

    >>> slots = [
    ...    {'task': 'admin',
    ...     'start': datetime.datetime(2012, 2, 11, 12, 51)
    ...    }]
    >>> task = 'lunch'
    >>> time = datetime.datetime(2012, 2, 11, 11)
    >>> validate_time(slots, task, time)
    Traceback (most recent call last):
    ...
    TimeSheetError: Task lunch cannot start before admin

    >>> time = datetime.datetime(2012, 2, 13, 15)
    >>> validate_time(slots, task, time)

    """
    if not time > slots[-1]['start']:
        raise TimeSheetError(
            "Task %s cannot start before %s" % (task, slots[-1]['task']))


def print_summary(slots):
    total_time = ZERO
    for time, task, task_slots in sorted(group_by_task(slots)):
        if args.afk or task not in AFK:
            print '{0}: {1}'.format(humanize_time(time), task)
            total_time += time
            if args.verbose:
                for s in task_slots:
                    print s['note']
    print 'TOTAL: %s' % humanize_time(total_time)
    print


def humanize_time(timedelta):
    """
    Return ``timedelta`` in a human readable format.

    >>> t = datetime.timedelta(seconds=24 * 3600 + 3 * 3600 + 1200)
    >>> humanize_time(t)
    '27 hours, 20 minutes'

    >>> t = datetime.timedelta(seconds=3600)
    >>> humanize_time(t)
    '1 hour'

    >>> t = datetime.timedelta(seconds=480)
    >>> humanize_time(t)
    '8 minutes'

    """
    hours = timedelta.days * 24 + timedelta.seconds / 3600
    minutes = timedelta.seconds % 3600 / 60
    time = ''
    if hours:
        time += "{0} hour{1}".format(hours, "s" if hours > 1 else "")
    if minutes:
        if time:
            time += ', '
        time += "{0} minutes".format(minutes)
    return time


def date_from_file_path(file_path):
    """
    Return ``datetime`` from file name in YYYYMMDD.<ext> format.

    >>> file_path = '/Users/mark/weekly/20120211.txt'
    >>> date_from_file_path(file_path)
    datetime.datetime(2012, 2, 11, 0, 0)

    """
    file_name = os.path.splitext(
        os.path.basename(file_path))[0]
    return datetime.datetime.strptime(file_name, "%Y%m%d")


def group_by_task(slots):
    return (
        _annotate_task_group(t, g) for t, g in
        groupby(sorted(slots, key=itemgetter('task')), lambda x: x['task']))


def group_by_day(slots):
    return groupby(slots, lambda x: x['start'].strftime('%A'))


def group_by_week(slots):
    return groupby(slots, lambda x: x['start'].strftime('%W'))


def group_by_month(slots):
    return groupby(slots, lambda x: x['start'].strftime('%B'))


def _annotate_task_group(task, group):
    # assumes group is from groupby!
    g = list(group)
    return sum([s['end'] - s['start'] for s in g], ZERO), task, g


def main():
    slots = []
    for path in sorted(args.timesheet):
        start_date = date_from_file_path(path)
        with open(path) as f:
            slots.extend(parse(start_date, f))
    print_summary(slots)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a time sheet.')
    parser.add_argument('timesheet',
                        nargs='+',
                        help='path to time sheet file')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help="show verbose output in summary")
    parser.add_argument('--afk', dest='afk', action='store_true',
                        help="include time spent AFK")
    args = parser.parse_args()
    main()
