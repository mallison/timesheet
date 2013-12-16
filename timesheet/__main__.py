import argparse
import glob
import os
from datetime import date, datetime, timedelta

import filters
import report
from timesheet import Timesheet


def main():
    parser = argparse.ArgumentParser(description='Timesheet reports.')
    parser.add_argument('timesheet',
                        nargs='*',
                        help='path to time sheet file')
    parser.add_argument('-l', '--level', type=int, default=1)
    parser.add_argument('--since', type=_date_type)
    parser.add_argument('--until', type=_date_type)
    parser.add_argument('--stand-up', action='store_true')
    parser.add_argument('--eom', action='store_true')
    parser.add_argument('-r', '--resolution',
                        nargs='*',
                        choices=report.DATE_FORMAT)
    parser.add_argument('-t', '--task',)
    parser.add_argument('-c', '--commits', action='store_true',
                        help="show commits to repo")
    args = parser.parse_args()

    if args.eom:
        timesheet = _read_files(_get_eom_timesheet_paths())
    elif args.timesheet:
        timesheet = _read_files(args.timesheet)
    else:
        timesheet = _read_files(_get_current_timesheet_paths())

    if args.stand_up:
        timesheet = filters.stand_up(timesheet)
        resolution = ['day']
    else:
        resolution = args.resolution
        if args.since:
            timesheet = filters.from_(timesheet, args.since)
        if args.until:
            timesheet = filters.to(timesheet, args.until)
    if args.task:
        timesheet = filters.task(
            timesheet, tuple(task.strip() for task in args.task.split(':')))
    report.show_groups(timesheet,
                       resolutions=resolution,
                       task_level=args.level,
                       show_commits=args.commits)


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


def _get_current_timesheet_paths():
    today = datetime.today()
    delta = today.weekday()
    this_week = today - timedelta(days=delta)
    last_week = this_week - timedelta(days=7)
    return ['/Users/user/thebbgroup/weekly/{:%Y%m%d}.org'.format(d)
            for d in last_week, this_week]


def _get_eom_timesheet_paths():
    today = date.today()
    return glob.glob('/Users/user/thebbgroup/weekly/%s*org' %
                     today.strftime('%Y%m'))


def _datetime_from_filename(path):
    filename = os.path.basename(path)
    return datetime(int(filename[:4]),
                    int(filename[4:6]),
                    int(filename[6:8]))


if __name__ == '__main__':
    main()
