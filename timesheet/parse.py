"""
Summarise task log by time period(s)
"""
import datetime
import os
import re

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_START = re.compile(r'^(' + '|'.join(DAYS) + ')$')
TASK_START = re.compile(r'^(\d{4}) ?(.*)$')

def read_timesheets(timesheet_paths, granularity, max_depth):
    slots = []
    for path in timesheet_paths:
        base_date = _get_start_date_from_file_name(path)
        slots.extend(_read_timesheet(base_date, path))
    return slots


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
            time_in_minutes = hhmm_to_minutes(clock_time)
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


def hhmm_to_minutes(hhmm):
    if hhmm == '9999':
        hhmm = get_current_time()
    return 60 * int(hhmm[:2]) + int(hhmm[2:])


def get_current_time():
    return datetime.now().strftime('%H%M')

