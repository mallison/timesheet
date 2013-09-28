import argparse
import os
from datetime import datetime, timedelta
from pprint import pprint

import filters
from timesheet import Timesheet


def main():
    parser = argparse.ArgumentParser(description='Timesheet reports.')
    parser.add_argument('timesheet',
                        nargs='*',
                        help='path to time sheet file')
    parser.add_argument('-l', '--level', type=int, default=1)
    parser.add_argument('--since', type=_date_type)
    parser.add_argument('--until', type=_date_type)
    parser.add_argument('--stand-up')
    parser.add_argument('-t', '--task',)
    parser.add_argument('-c', '--commits', action='store_true',
                        help="show commits to repo")
    args = parser.parse_args()

    if args.timesheet:
        timesheet = _read_files(args.timesheet)
    else:
        timesheet = _read_files([_get_current_timesheet_path()])

    if args.stand_up:
        timesheet = filters.standup(timesheet, args.until)
    else:
        if args.since:
            timesheet = filters.from_(timesheet, args.since)
        if args.until:
            timesheet = filters.to(timesheet, args.until)
    if args.task:
        timesheet = filters.task(
            timesheet, tuple(task.strip() for task in args.task.split(':')))
    pprint(list(timesheet))


def _date_type(date_arg):
    return datetime.strptime(date_arg, "%Y-%m-%d")


def _read_files(paths):
    timesheet = None
    for path in paths:
        with open(path) as f:
            new_timesheet = Timesheet(_datetime_from_filename(path), f)
            if timesheet is None:
                timesheet = new_timesheet
            else:
                timesheet.extend(new_timesheet)
    return timesheet


def _get_current_timesheet_path():
    today = datetime.today()
    delta = today.weekday()
    return '/Users/mark/Dropbox/work/thebbgroup/weekly/{:%Y%m%d}.org'.format(
        today - timedelta(days=delta))


def _datetime_from_filename(path):
    filename = os.path.basename(path)
    return datetime(int(filename[:4]),
                    int(filename[4:6]),
                    int(filename[6:8]))


if __name__ == '__main__':
    main()
