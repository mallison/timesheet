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
        level.setdefault(part, {
            'slots': [],
            'duration': 0,
            'subtasks': {},
        })['slots'].append(task)
        level[part]['duration'] += _get_time(task)
        level = level[part]['subtasks']


def is_last_task_open():
    return len(TASKS) > 1 and 'end' not in TASKS[-1]


def remove_last_task():
    del TASKS[-1]
    

def is_end_of_timesheet(line):
    return '-' * 50 in line


def print_report(report, level=0):
    tasks = report.keys()
    tasks.sort(key=lambda t: -report[t]['duration'])
    for task in tasks:
        details = report[task]
        indent = ' ' * level * 4
        print '%-50s%s' % (
            indent + task,
            man_days(datetime.timedelta(minutes=details['duration'])))
        print_report(details['subtasks'], level + 1)
    if level == 1:
        print


def _get_time(task):
    start = _time_to_int(task['start'])
    end = _time_to_int(task['end'])
    return end - start


def _time_to_int(time):
    return int(time[:2]) * 60 + int(time[-2:])


def man_days(delta):
    """
    Return ``timedelta`` in human readable man days.

    >>> import timedelta
    >>> t = timedelta(seconds=(3 * 7.5 * 3600) + (3 * 3600) + 1210)
    >>> man_days(t)
    '3 days, 3 hours, 20 minutes'

    >>> t = timedelta(seconds=3625)
    >>> man_days(t)
    '1 hour'

    >>> t = timedelta(seconds=484)
    >>> man_days(t)
    '8 minutes'

    """
    minutes = (delta.days * 24 * 3600 + delta.seconds) / 60
    # days, minutes = divmod(minutes, MAN_DAY * 60)
    hours, minutes = divmod(minutes, 60)
    out = []
    for measure, amount in zip(("h", "m"),
                               (hours, minutes)):
        if amount:
            out.append("{:.0f}{}".format(amount, measure))
    return " ".join(out)
