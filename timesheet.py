import datetime
import os
import re
import subprocess
import sys

DAYS = [datetime.date(2014, 2, d).strftime('%A') for d in range(3, 10)]
TASK_START_REGEX = re.compile(r'(\d{4})')
REFLOG_RE = re.compile(r'^[0-9a-f]+ .*?\{([\d\-: ]+) \+.*?: (.*)$')
AFK = ['lunch', 'afk']

TASKS = []
REPORT = {}
REFLOG = {}

                    
def main(file_path):
    _set_start_date_from_file_name(file_path)
    _read_reflog()
    with open(file_path) as f:
        for line in f:
            _handle_line(line)


def _set_start_date_from_file_name(file_path):
    global START_DATE
    file_name = os.path.splitext(
        os.path.basename(file_path))[0]
    START_DATE = datetime.datetime.strptime(file_name, '%Y%m%d')


def _handle_line(line):
    try:
        day = _get_day(line)
    except ValueError:
        try:
            timestamp, task = _get_timestamp_and_task(line)
        except AttributeError:
            if _is_end_of_timesheet(line):
                _close_current_day()
                _report_current_day()
            elif _is_current_task_open():
                _add_line_to_task_notes(line)
        else:
            if _is_current_task_open():
                _close_current_task(timestamp)
            _start_task(timestamp, task)
    else:
        if _is_current_task_open():
            _close_current_day()
            _report_current_day()
        _update_current_day(day)



def _get_day(line):
    day = line.strip()
    if day in DAYS:
        return day
    else:
        raise ValueError("line doesn't start day")


def _get_timestamp_and_task(line):
    m = TASK_START_REGEX.match(line)
    timestamp = m.group(1)
    task = line.replace(timestamp, '').strip()
    timestamp = datetime.datetime.combine(
        CURRENT_DATE, datetime.time(int(timestamp[:2]), int(timestamp[-2:])))
    return timestamp, task


def _update_current_day(day):
    global START_DATE, CURRENT_DATE
    CURRENT_DATE = START_DATE + datetime.timedelta(DAYS.index(day))


def _start_task(timestamp, name):
    task = dict(
        name=name,
        start=timestamp,
        notes=[],
        # TODO commits=[],
    )
    TASKS.append(task)


def _add_line_to_task_notes(line):
    TASKS[-1]['notes'].append(line)


def _is_current_task_open():
    return TASKS and 'end' not in TASKS[-1]


def _close_current_task(timestamp):
    task = TASKS[-1]
    task['end'] = timestamp
    parts = [t.strip() for t in task['name'].split(':')]
    level = REPORT
    for part in parts:
        if not part:
            part = 'misc'
        level.setdefault(part, {
            'slots': [],
            'duration': datetime.timedelta(0),
            'subtasks': {},
        })['slots'].append(task)
        level[part]['duration'] += _get_duration(task)
        level = level[part]['subtasks']


def _get_duration(task):
    return task['end'] - task['start']
    

def _close_current_day():
    global TASKS
    del TASKS[-1]


def _report_current_day():
    global REPORT, TASKS
    day = TASKS[-1]['start'].strftime('%A')
    for afk in AFK:
        if afk in REPORT:
            del REPORT[afk]
    print '#' * 70
    print day
    print '#' * 70
    _print_report(REPORT)
    REPORT = {}
    TASKS = []


def _is_end_of_timesheet(line):
    return '-' * 50 in line


def _print_report(report, level=0):
    tasks = report.keys()
    tasks.sort(key=lambda t: -report[t]['duration'])
    if level == 0:
        overall = sum((d['duration'] for d in report.values()), datetime.timedelta(0))
        print '%-50s%s' % ('OVERALL', _man_days(overall))
        print '-' * 70
    for task in tasks:
        details = report[task]
        indent = ' ' * level * 2
        print '%-50s%s' % (
            indent + task,
            _man_days(details['duration']))
        reflog = []
        for slot in details['slots']:
            reflog.extend(
                i for i in REFLOG.items()
                if slot['start'] <= i[0] < slot['end']
            )
        reflog.sort()
        if reflog:
            print ('\n' + indent).join(l[1] for l in reflog)
        _print_report(details['subtasks'], level + 1)
    if level == 1:
        print


def _man_days(delta):
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


def _read_reflog():
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


if __name__ == '__main__':
    main(sys.argv[1])
