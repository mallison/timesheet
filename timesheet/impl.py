import datetime
import re
import sys

DAYS = [datetime.date(2014, 2, d).strftime('%b') for d in range(3, 11)]
TASK_START_REGEX = re.compile(r'(\d{4})')

TASKS = []
REPORT = {}

                    
def main(line_handler_func):
    with open(sys.argv[1]) as f:
        for line in f:
            line_handler_func(line)
    print_report(REPORT)


def get_day(line):
    day = line.split(' ', 1)[0]
    if day in DAYS:
        return day


def validate_day(line):
    pass


def get_timestamp_and_task(line):
    m = TASK_START_REGEX.match(line)
    timestamp = m.group(1)
    return timestamp, line.replace(timestamp, '').strip()


def set_datetime_to_this_day():
    pass


def start_task(timestamp, name):
    task = dict(
        name=name,
        start=timestamp,
        notes=[],
        # TODO commits=[],
    )
    TASKS.append(task)


def add_line_to_task_notes(line):
    TASKS[-1]['notes'].append(line)


def close_last_task(timestamp):
    task = TASKS[-1]
    task['end'] = timestamp
    parts = [t.strip() for t in task['name'].split(':')]
    level = REPORT
    for part in parts:
        level.setdefault(part, {'tasks': []})['tasks'].append(task)
        level = level[part]


def is_last_task_open():
    return len(TASKS) > 1 and 'end' not in TASKS[-1]


def remove_last_task():
    del TASKS[-1]
    

def is_end_of_timesheet(line):
    return '-' * 50 in line


def print_report(report, level=0):
    for task, details in report.items():
        if task == 'tasks':
            continue
        indent = ' ' * level * 4
        print '%s%s' % (indent, task)
        print_report(details, level + 1)
    if level == 1:
        print
