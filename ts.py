import re
import sys

import utils

DAY_START = re.compile(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|\d{1,2}/\d{1,2}/\d{2})$')
TASK_START = re.compile(r'^(\d{4}) ?(.*)$')


def main():
    tally = {}
    for line in sys.stdin.readlines():
        day_match = DAY_START.match(line)
        task_match = TASK_START.match(line)
        if day_match:
            start = None
            day = day_match.group(1)
        elif task_match:
            time = utils.hhmm_to_minutes(task_match.group(1))
            if start:
                add_interval_to_tally(tally, day, task, start, time)
            start = time
            task = task_match.group(2) or 'misc'
    utils.print_task('main', tally['main'])


def add_interval_to_tally(tally, day, task, start, end):
    sub_tasks = [t.strip() for t in task.split(':')]
    if sub_tasks[0] in ['afk', 'lunch']:
        return
    interval = get_interval(start, end)
    sub_task_tally = tally
    for sub_task in ['main', day] + sub_tasks:
        sub_task_tally.setdefault(
            sub_task, get_task())['total'] += interval
        sub_task_tally = sub_task_tally[sub_task]['sub']


def get_interval(start, end):
    if end < start:
        # assume wraps around midnight
        interval = 24 * 60 - start + end
    else:
        interval = end - start
    return interval


def get_task():
    return {
        'total': 0,
        'sub': {}
    }


if __name__ == '__main__':
    main()
