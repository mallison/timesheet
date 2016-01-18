"""
Summarise task log by time period(s)
"""
import argparse
import datetime
import itertools
import os
import re

import utils

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_UNITS = ['year', 'month', 'week', 'day']
AFK = ['lunch', 'afk']
DAY_START = re.compile(r'^(' + '|'.join(DAYS) + ')$')
TASK_START = re.compile(r'^(\d{4}) ?(.*)$')

def main():
    parser = argparse.ArgumentParser(description='Timesheet')
    parser.add_argument('timesheet',
                        nargs='*',
                        help='path to time sheet file(s)')
    parser.add_argument('-g', '--granularity',
                        action='append',
                        choices=TIME_UNITS)
    parser.add_argument('-d', '--max-depth', type=int, default=1)
    args = parser.parse_args()
    granularity = [u for u in TIME_UNITS if u in args.granularity]
    read_timesheets(
        args.timesheet,
        granularity=granularity,
        max_depth=args.max_depth
    )


def read_timesheets(timesheet_paths, granularity, max_depth):
    slots = []
    for path in timesheet_paths:
        base_date = _get_start_date_from_file_name(path)
        slots.extend(_read_timesheet(base_date, path))
    _report(slots, granularity, max_depth)


def _read_timesheet(base_date, timesheet_path):
    with open(timesheet_path) as f:
        return _read_timesheet_lines(base_date, f.readlines())


def _read_timesheet_lines(base_date, lines):
    for line in lines:
        day_match = DAY_START.match(line)
        task_match = TASK_START.match(line)
        if day_match:
            start = None
            day = day_match.group(1)
            date = base_date + datetime.timedelta(DAYS.index(day))
        elif task_match:
            clock_time = task_match.group(1)
            time_in_minutes = utils.hhmm_to_minutes(clock_time)
            if start:
                timestamp = datetime.datetime.combine(
                    date, datetime.time(int(clock_time[:2]), int(clock_time[-2:]))
                )
                yield (
                    timestamp,
                    [t.strip() for t in task.split(':')],
                    _get_interval(start, time_in_minutes)
                )
            start = time_in_minutes
            task = task_match.group(2) or 'misc'

    
def _get_start_date_from_file_name(file_path):
    file_name = os.path.splitext(
        os.path.basename(file_path))[0]
    return datetime.datetime.strptime(file_name, '%Y%m%d').date()


def _get_interval(start, end):
    if end < start:
        # assume wraps around midnight
        interval = 24 * 60 - start + end
    else:
        interval = end - start
    return interval


def _report(slots, granularity, max_depth=1, indent=0):
    time_unit = granularity[0]
    key_func = _get_key_func(time_unit)
    for period, slots_in_period in itertools.groupby(slots, key_func):
        report = {}
        slots_in_period = list(slots_in_period)
        for slot in slots_in_period:
            task = slot[1]
            if task[0] in AFK:
                continue
            level = report
            levels = ['main'] + task[:max_depth]
            for subtask in levels:
                if not subtask:
                    subtask = 'misc'
                level.setdefault(subtask, {
                    'duration': 0,
                    'subtasks': {},
                })
                level[subtask]['duration'] += slot[2]
                level = level[subtask]['subtasks']
        utils.print_task(period, report['main'], indent=indent)
        print
        if len(granularity) > 1:
            _report(slots_in_period, granularity[1:], max_depth, indent +  4)


def _get_key_func(granularity):
    if granularity == 'day':
        return lambda slot: slot[0].date().strftime('%a %d %b')
    if granularity == 'week':
        return lambda slot: '%s WW%s' % slot[0].date().isocalendar()[:2]
    if granularity == 'month':
        return lambda slot: slot[0].date().strftime('%b %Y')
    if granularity == 'year':
        return lambda slot: str(slot[0].date().year)
    raise ValueError("Granularity '%s' is not valid" % granularity)


if __name__ == '__main__':
    main()
