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


def summarise(slots):
    """
    Return a dictionary keyed by task the value of which is a list
    with the total time spent and the notes concatenated together.

    >>> slots = parse(datetime.datetime(2012, 2, 6, 0, 0), '''
    ... Monday
    ... 0900 email
    ... 0920 moderation
    ... 1100 tea
    ... 1115 moderation
    ... 1300 lunch
    ... 1400 weekly meeting
    ... 1600 moderation
    ... 1730
    ... '''.splitlines(1))

    >>> summarise(slots) == \
    {
    ...     'email': [datetime.timedelta(0, 1200), ''],
    ...     'moderation': [datetime.timedelta(0, 17700), ''],
    ...     'tea': [datetime.timedelta(0, 900), ''],
    ...     'weekly meeting': [datetime.timedelta(0, 7200), ''],
    ...     'lunch': [datetime.timedelta(0, 3600), ''],
    ... }
    True

    """
    # TODO use groupby here!!!
    summary = {}
    for slot in slots:
        task = slot['task']
        time = slot['end'] - slot['start']
        summary.setdefault(task, [datetime.timedelta(0), ''])[0] += time
        summary[task][1] += slot['note']
    return summary


def print_summary(summary):
    total_time = datetime.timedelta(0)
    for task, (time, notes) in sorted(
        summary.items(), key=itemgetter(1)):
        if args.afk or task not in AFK:
            print '%s: %s' % (humanize_time(time), task)
            if args.verbose:
                for line in notes.splitlines():
                    print '    %s' % line
            total_time += time
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


def main():
    start_date = date_from_file_path(args.timesheet)
    with open(args.timesheet) as f:
        slots = parse(start_date, f)
    if args.daily:
        for k, g in groupby(slots, lambda x: x['start'].strftime('%A')):
            print k
            print_summary(summarise(g))
    print 'Week'
    print_summary(summarise(slots))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a time sheet.')
    parser.add_argument('timesheet',
                        help='path to time sheet file')
    parser.add_argument('-d', '--daily', action='store_true',
                        help="show summary per day")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help="show verbose output in summary")
    parser.add_argument('--afk', dest='afk', action='store_true',
                        help="include time spent AFK")
    args = parser.parse_args()
    main()
