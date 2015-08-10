import re
import sys

import utils

DAY_START = re.compile(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|\d{1,2}/\d{1,2}/\d{2})$')
TASK_START = re.compile(r'^(\d{4}) ?(.*)$')


def main():
    tally = {}
    for line in sys.stdin.readlines():
        m = DAY_START.match(line)
        if m:
            start = None
            day = m.group(1)
        m = TASK_START.match(line)
        if m:
            time = utils.hhmm_to_minutes(m.group(1))
            if start:
                parts = [p.strip() for p in task.split(':')]
                if parts[0] not in ['afk', 'lunch']:
                    sub_task = tally
                    for part in ['main', day] + parts:
                        if time < start:
                            # assume wraps around midnight
                            interval = 24 * 60 - start + time
                        else:
                            interval = time - start
                        sub_task.setdefault(
                            part, get_task())['total'] += interval
                        sub_task = sub_task[part]['sub']
            start = time
            task = m.group(2) or 'misc'
    utils.print_task('main', tally['main'])


def get_task():
    return {
        'total': 0,
        'sub': {}
    }


if __name__ == '__main__':
    main()