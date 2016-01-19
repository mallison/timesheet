import datetime
import os
import re
from collections import namedtuple

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_START = re.compile(r'^(' + '|'.join(DAYS) + ')$')
TASK_START = re.compile(r'^(\d{4}) ?(.*)$')

Slot = namedtuple('Slot', "timestamp task duration")

def read_timesheets(timesheet_paths):
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
            time_in_minutes = _hhmm_to_minutes(clock_time)
            if start:
                timestamp = _get_timestamp(date, clock_time)
                yield Slot(
                    timestamp,
                    [t.strip() for t in task.split(':')],
                    _get_duration(start, time_in_minutes)
                )
            start = time_in_minutes
            task = task_match.group(2) or 'misc'


def _get_start_date_from_file_name(file_path):
    file_name = os.path.splitext(
        os.path.basename(file_path))[0]
    return datetime.datetime.strptime(file_name, '%Y%m%d').date()


def _hhmm_to_minutes(hhmm):
    if hhmm == '9999':
        hhmm = _get_current_time()
    return 60 * int(hhmm[:2]) + int(hhmm[2:])


def _get_current_time():
    return datetime.datetime.now().strftime('%H%M')


def _get_timestamp(date, hhmm):
    return datetime.datetime.combine(
        date, datetime.time(int(hhmm[:2]), int(hhmm[-2:]))
    )


def _get_duration(start, end):
    if end < start:
        # assume wraps around midnight
        duration = 24 * 60 - start + end
    else:
        duration = end - start
    return duration
