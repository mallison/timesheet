import argparse
from datetime import datetime, timedelta

import parse
import report
import utils

# TODO bug tracker integration


def main():
    slots = parse_files()
    report.show_groups(list(since(slots)),
                       resolutions=args.resolution,
                       task_level=args.level,
                       show_commits=args.commits)


def parse_files():
    slots = []
    for path in get_timesheet_paths():
        slots.extend(parse_file(path))
    return slots


def get_timesheet_paths():
    if args.timesheet:
        timesheets = args.timesheet
    else:
        timesheets = [_get_default_timesheet()]
    return timesheets


def parse_file(path):
    with open(path) as f:
        try:
            start_date = utils.start_date_from_file_name(f.name)
        except ValueError:
            return []  # TODO warn?
        try:
            return parse.parse(f, start_date)
        except IndexError:
            return []  # TODO warn


def since(slots):
    return (s for s in slots if not args.since or s.start >= args.since)


def _get_default_timesheet():
    today = datetime.today()
    delta = today.weekday()
    return '/Users/mark/Dropbox/work/thebbgroup/weekly/{:%Y%m%d}.org'.format(
        today - timedelta(days=delta))


def date_type(date_arg):
    return datetime.strptime(date_arg, "%Y-%m-%d")


parser = argparse.ArgumentParser(description='Process a time sheet.')
parser.add_argument('timesheet',
                    nargs='*',
                    help='path to time sheet file')
parser.add_argument('-r', '--resolution',
                    nargs='*',
                    choices=report.DATE_FORMAT,
                    )
parser.add_argument('-l', '--level', type=int, default=1)
parser.add_argument('--since', type=date_type)
parser.add_argument('-c', '--commits', action='store_true',
                    help="show commits to repo")
args = parser.parse_args()
main()
