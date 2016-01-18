"""
Summarise task log by time period(s)
"""
import argparse

import parse
import report

TIME_UNITS = ['year', 'month', 'week', 'day']

def main():
    parser = argparse.ArgumentParser(description='Timesheet')
    parser.add_argument('timesheet',
                        nargs='*',
                        help='path to time sheet file(s)')
    parser.add_argument('-g', '--granularity',
                        action='append',
                        choices=TIME_UNITS)
    parser.add_argument('-d', '--max-depth', type=int, default=1)
    args = parser.parse_args()
    granularity = [u for u in TIME_UNITS if u in args.granularity]
    slots = parse.read_timesheets(
        args.timesheet,
        granularity=granularity,
        max_depth=args.max_depth
    )
    report.report(slots, granularity, args.max_depth)

if __name__ == '__main__':
    main()
