import argparse
import datetime
import os
import re
from operator import itemgetter
from itertools import groupby

# TODO take list of files for summaries over longer than a week
# TODO could probably do the parsing with one cunning regexp (remember
# someone posted a perl prog to parse html with a regexp!)

DAYS = [datetime.date(2008, 9, _x).strftime('%A') for _x in range(1, 8)]
TASK_START_REGEXP = re.compile(r'^(\d{2})(\d{2})([ \w\/\.\-]*)$')
AFK = ['tea', 'lunch', 'afk']


class TimeSheetError(Exception):
    """Base class for errors in the timesheet module"""
    pass


def parse():
    # parse the time slots into a list
    slots = []
    current_day = None
    current_date = date_from_file_path(args.timesheet)
    with open(args.timesheet) as f:
        for line in f:
            line = line.strip()
            m = TASK_START_REGEXP.match(line)
            if line in DAYS:
                # Record for a new days starts
                if slots:
                    # If this is not the first day we'll have a bogus
                    # last slot created when then the clock out time
                    # for the previous days was parsed. Delete it.
                    del slots[-1]
                validate_day(slots, current_day, line)
                if current_day is not None:
                    current_date += datetime.timedelta(days=1)
                current_day = line
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


def validate_day(slots, current_day, next_day):
    if current_day is None and not next_day == DAYS[0]:
        raise TimeSheetError(
            "Week starts on %s not %s" % (DAYS[0], next_day, current_day))
    if current_day:
        if not DAYS.index(current_day) == DAYS.index(next_day) - 1:
            raise TimeSheetError(
                "%s does not follow %s" % (next_day, current_day))
        if 'end' not in slots[-1]:
            raise TimeSheetError(
                "No end time given for %s on %s" %
                (slots[-1]['task'], current_day))


def validate_time(slots, task, time):
    if not time > slots[-1]['start']:
        raise TimeSheetError(
            "Task %s cannot start before %s" % (task, slots[-1]['task']))


def summarize(slots):
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
            print '%s: %s' % (format_time(time), task)
            if args.verbose:
                for line in notes.splitlines():
                    print '    %s' % line
            total_time += time
    print 'TOTAL: %s' % format_time(total_time)
    print


def format_time(time):
    hours = time.days * 24 + time.seconds / 3600
    minutes = time.seconds % 3600 / 60
    time = ''
    if hours:
        time += "%s hours" % hours
    if minutes:
        if time:
            time += ', '
        time += "%s minutes" % minutes
    return time


def date_from_file_path(file_name):
    filename = os.path.splitext(
        os.path.basename(file_name))[0]
    return datetime.datetime.strptime(filename, "%Y%m%d")


def main():
    slots = parse()
    if args.daily:
        for k, g in groupby(slots, lambda x: x['start'].strftime('%A')):
            print k
            print_summary(summarize(g))
    print 'Week'
    print_summary(summarize(slots))


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
