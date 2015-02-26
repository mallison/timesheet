import argparse
import datetime
import itertools
import os
import re
import subprocess

DAYS = [datetime.date(2014, 2, d).strftime('%A') for d in range(3, 10)]
TASK_START_REGEX = re.compile(r'(\d{4})')
REFLOG_RE = re.compile(r'^[0-9a-f]+ .*?\{([\d\-: ]+) \+.*?: (.*)$')
AFK = ['lunch', 'afk']

TASKS = []
REFLOG = {}

START_DATE = CURRENT_DATE = None


class EndOfTimesheet(Exception):
    pass


def main():
    global START_DATE
    parser = argparse.ArgumentParser(description='Timesheet')
    parser.add_argument('timesheet',
                        nargs='*',
                        help='path to time sheet file')
    parser.add_argument('-l', '--level', type=int, default=0)
    parser.add_argument('-g', '--granularity',
                        default='day',
                        choices=['day', 'week', 'month', 'year'])
    parser.add_argument('-c', '--commits', action='store_true',
                        help="show commits to repo")
    args = parser.parse_args()

    _read_reflog()
    for path in args.timesheet:
        START_DATE = _get_start_date_from_file_name(path)
        with open(path) as f:
            for line in f:
                try:
                    _handle_line(line)
                except EndOfTimesheet:
                    break
    _report(
        granularity=args.granularity,
        show_commits=args.commits,
        max_level=args.level
    )


def _get_start_date_from_file_name(file_path):
    file_name = os.path.splitext(
        os.path.basename(file_path))[0]
    return datetime.datetime.strptime(file_name, '%Y%m%d').date()


def _handle_line(line):
    day = _get_day(line)
    if day:
        if _is_current_task_open():
            _close_current_day()
        _update_current_day(day)
    else:
        timestamp, task = _get_timestamp_and_task(line)
        if timestamp:
            if _is_current_task_open():
                _close_current_task(timestamp)
            _start_task(timestamp, task)
        elif _is_end_of_timesheet(line):
            _close_current_day()
            raise EndOfTimesheet
        elif _is_current_task_open():
            _add_line_to_task_notes(line)
        else:
            raise ValueError('Unexpected line %s' % line)

            
def _get_day(line):
    day = line.strip()
    if day in DAYS:
        return day


def _get_timestamp_and_task(line):
    m = TASK_START_REGEX.match(line)
    if not m:
        return None, None
    timestamp = m.group(1)
    task = line.replace(timestamp, '').strip()
    timestamp = datetime.datetime.combine(
        CURRENT_DATE, datetime.time(int(timestamp[:2]), int(timestamp[-2:])))
    return timestamp, task


def _update_current_day(day):
    global CURRENT_DATE
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


def _get_duration(task):
    return task['end'] - task['start']
    

def _close_current_day():
    del TASKS[-1]


def _is_end_of_timesheet(line):
    return '-' * 50 in line


def _report(granularity='day', show_commits=False, max_level=1):
    key_func = globals()['_by_%s' % granularity]
    for period, tasks in itertools.groupby(TASKS, key_func):
        report = {}
        for task in tasks:
            parts = [t.strip() for t in task['name'].split(':')]
            if parts[0] in AFK:
                continue
            level = report
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
        _print_report(period, report, show_commits=show_commits, max_level=max_level)


def _by_day(task):
    return task['start'].date()


def _by_week(task):
    isocalendar = task['start'].date().isocalendar()
    return isocalendar[:2]


def _by_month(task):
    date = task['start'].date()
    return date.year, date.month


def _by_year(task):
    date = task['start'].date()
    return date.year


def _print_report(period, report, level=0, max_level=0, show_commits=False):
    tasks = report.keys()
    tasks.sort(key=lambda t: -report[t]['duration'])
    if level == 0:
        overall = sum((d['duration'] for d in report.values()), datetime.timedelta(0))
        print '%-50s%s' % (period, _man_days(overall))
        print '-' * 70
    for task in tasks:
        details = report[task]
        indent = ' ' * level * 2
        print '%-50s%s' % (
            indent + task,
            _man_days(details['duration']))
        if show_commits:
            reflog = []
            for slot in details['slots']:
                reflog.extend(
                    i for i in REFLOG.items()
                    if slot['start'] <= i[0] < slot['end']
                )
            reflog.sort()
            if reflog:
                print ('\n' + indent).join(l[1] for l in reflog)
        if level < max_level:
            _print_report(period, details['subtasks'], level + 1, max_level=max_level, show_commits=show_commits)
    if level == 0:
        print
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
        cwd='/Users/user/di/src',
    )
    for line in contents.splitlines():
        m = REFLOG_RE.match(line)
        if m and 'commit' in m.group(2):
            timestamp = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
            REFLOG[timestamp] = m.group(2)


if __name__ == '__main__':
    main()
