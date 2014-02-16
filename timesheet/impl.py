import datetime
import re
import subprocess
import sys

DAYS = [datetime.date(2014, 2, d).strftime('%A') for d in range(3, 10)]
TASK_START_REGEX = re.compile(r'(\d{4})')
REFLOG_RE = re.compile(r'^[0-9a-f]+ .*?\{([\d\-: ]+) \+.*?: (.*)$')

DATE = datetime.date(2014, 2, 2)
TASKS = []
REPORT = {}
REFLOG = {}

                    
def main(line_handler_func):
    with open(sys.argv[1]) as f:
        for line in f:
            line_handler_func(line)
    read_reflog()
    print_report(REPORT)


def get_day(line):
    day = line.strip()
    if day in DAYS:
        return day


def validate_day(line):
    pass


def get_timestamp_and_task(line):
    m = TASK_START_REGEX.match(line)
    timestamp = m.group(1)
    task = line.replace(timestamp, '').strip()
    timestamp = datetime.datetime.combine(
        DATE, datetime.time(int(timestamp[:2]), int(timestamp[-2:])))
    return timestamp, task


def set_datetime_to_this_day(day):
    global DATE
    # TODO days might be skipped
    DATE += datetime.timedelta(1)


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
            'duration': datetime.timedelta(0),
            'subtasks': {},
        })['slots'].append(task)
        level[part]['duration'] += _get_duration(task)
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
        indent = ' ' * level * 2
        print '%-50s%s' % (
            indent + task,
            man_days(details['duration']))
        reflog = []
        for slot in details['slots']:
            reflog.extend(
                i for i in REFLOG.items()
                if slot['start'] <= i[0] < slot['end']
            )
        reflog.sort()
        if reflog:
            print ('\n' + indent).join(l[1] for l in reflog)
        print_report(details['subtasks'], level + 1)
    if level == 1:
        print


def _get_duration(task):
    return task['end'] - task['start']


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


def read_reflog():
    global REFLOG
    contents = subprocess.check_output(
        ['git', 'reflog', '--date', 'iso', '--all'],
        cwd='/Users/user/thebbgroup/cosmo',
    )
    for line in contents.splitlines():
        m = REFLOG_RE.match(line)
        if m and 'commit' in m.group(2):
            timestamp = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
            REFLOG[timestamp] = m.group(2)
