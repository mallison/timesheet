import argparse
import itertools
import os
import pickle
import re
import sys
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from operator import itemgetter

# TODO bug tracker integration
# TODO change TRUNC_DATE to a dict and remove 'urgh' occurences!

SLOT_REGEXP = re.compile(
    r"""
    (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*
    (\d{4})\ ?(.*?)\n
    (.*?)
    (?=\n(\d{4})|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)
    """, re.DOTALL | re.X)
AFK = ['afk', 'tea', 'lunch']
TRUNC_DATE = (
    ('year', lambda d: datetime(d.year, 1, 1), "%Y"),
    ('month', lambda d: datetime(d.year, d.month, 1), "%b %Y"),
    # TODO ('week', lambda d: datetime(????), "%U %Y"),
    ('day', lambda d: datetime(d.year, d.month, d.day), "%a %b %d, %Y")
)
MAN_DAY = 7.5  # hours
NOTES_DELIMITER = '-' * 50
COMMIT_LOG = os.path.expanduser('~/.gitlog')

Slot = namedtuple('Slot', "start end task note")


def parse_file(file):
    start_date = datetime.strptime(
        os.path.splitext(os.path.basename(file.name))[0], "%Y%m%d")
    # TODO can I avoid file.read() -- finditer doesn't like file objects?
    timesheet = remove_notes(file.read())
    return parse(timesheet, start_date)


def remove_notes(content):
    if NOTES_DELIMITER in content:
        return content.split(NOTES_DELIMITER)[0]
    return content


def parse(string, start_date):
    return validate(convert_to_datetime(raw_parse(string), start_date))


def raw_parse(string):
    for m in re.finditer(SLOT_REGEXP, string):
        yield m.groups()


def convert_to_datetime(slots, start_date):
    """
    Convert start and end times to datetime objects.
    """
    for day, start, task, note, end in slots:
        if day and day != "Monday":
            start_date += timedelta(days=1)
        if end:  # TODO fix regexp to not grab end of day as a task!
            yield Slot(start_date + to_timedelta(start),
                       start_date + to_timedelta(end),
                       split_hierarchical_tasks(task),
                       note,
                       )


def split_hierarchical_tasks(task):
    return tuple((t.strip() for t in task.split(':')))


def validate(slots):
    prev_slot = None
    current_days_slots = []

    for slot in slots:
        if slot.end < slot.start:
            print >>sys.stderr, "incorrect end time for slot"

        if prev_slot:
            if slot_not_in_current_day(prev_slot, slot):
                if not current_day_follows_previous(prev_slot, slot):
                    print >>sys.stderr, "days out of sequence: %s -> %s" % (prev_slot.start, slot.start)
                length_of_day = sum((s.end - s.start for s in current_days_slots if s.task[0].lower() not in AFK), timedelta(0))
                if length_of_day < timedelta(hours=MAN_DAY):
                    print >>sys.stderr, "short day %s %s" % (length_of_day, current_days_slots[-1].end - current_days_slots[0].start)
                current_days_slots = []

        current_days_slots.append(slot)
        prev_slot = slot

        if slot.task[0].lower() not in AFK:  # TODO make afk filter optional
            if slot.task[0] == '':
                slot = Slot(slot.start, slot.end, ("misc",), slot.note)
            yield slot


def slot_not_in_current_day(previous_slot, current_slot):
    return current_slot.start.day != previous_slot.start.day


def current_day_follows_previous(previous_slot, current_slot):
    return previous_slot.start.toordinal() + 1 == current_slot.start.toordinal()



def group(slots, resolution):
    """Group slots by year, month, day.

    Returns a mapping of the form:

    grouped[<datetime>] = [<slot>, <slot>, ...]

    """
    urgh = dict((t[:2] for t in TRUNC_DATE))[resolution]
    return itertools.groupby(slots, lambda x: urgh(x.start))


def show_groups(slots, resolutions=None):
    for resolution in resolutions or [None]:
        if resolution is not None:
            grouped = group(slots, resolution)
            urgh = dict(((t[0], t[2]) for t in TRUNC_DATE))[resolution]
        else:
            grouped = ('All', slots),
            urgh = None
        for date, slots in grouped:
            print
            print urgh and date.strftime(urgh) or date
            summarize(slots)


def summarize(slots):
    totals = defaultdict(lambda: timedelta(0))
    overall = timedelta(0)
    slots = list(slots)  # TODO trying to avoid this!
    for slot in slots:
        duration = slot.end - slot.start
        totals[slot.task[:args.level]] += duration
        overall += duration
    most = max([t[1] for t in totals.items()])
    for task, total in sorted(totals.items(), key=itemgetter(1)):
        print "{:30s} {:15s} {}".format(
            ': '.join(task)[:30],
            man_days(total),
            "#" * int(50 * total.total_seconds() / most.total_seconds())
            )
        if args.commits:
            for slot in slots:
                if slot.task == task:
                    print_commits(slot)
            print
    print "{:30s} {}".format("OVERALL", man_days(overall))


def print_commits(slot):
    commits = [c for c in COMMITS if slot.start <= c[0] < slot.end]
    for time, msg in commits:
        msg = re.sub(r'^#.*$', '', msg, flags=re.M).strip()
        print "    {0:%H%M} {1:}".format(time, msg)


def minutes(time_string):
    """Convert a string in HHMM format to a number of minutes.

    >>> minutes("1341")
    821
    """
    return int(time_string[:2]) * 60 + int(time_string[2:])


def to_timedelta(time_string):
    """Convert a string in HHMM format to a timedelta.

    >>> to_timedelta("0832")
    datetime.timedelta(0, 30720)
    """
    return timedelta(seconds=minutes(time_string) * 60)


def man_days(delta):
    """
    Return ``timedelta`` in human readable man days.

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
    days, minutes = divmod(minutes, MAN_DAY * 60)
    hours, minutes = divmod(minutes, 60)
    out = []
    for measure, amount in zip(("d", "h", "m"),
                               (days, hours, minutes)):
        if amount:
            out.append("{:.0f}{}".format(amount, measure))
    return " ".join(out)


def since(slots):
    return (s for s in slots if not args.since or s.start >= args.since)


def date_type(date_arg):
    return datetime.strptime(date_arg, "%Y-%m-%d")


def main():
    slots = []
    if args.timesheet:
        timesheets = args.timesheet
    else:
        timesheets = [_get_default_timesheet()]
    for path in timesheets:
        with open(path) as f:
            slots.extend(parse_file(f))
    show_groups(since(slots), args.resolution)


def _get_default_timesheet():
    today = datetime.today()
    delta = today.weekday()
    return '/home/mark/bb/weekly/{:%Y%m%d}.org'.format(
        today - timedelta(days=delta))


if __name__ == '__main__':
    with open(COMMIT_LOG) as f:
        COMMITS = pickle.load(f)
    parser = argparse.ArgumentParser(description='Process a time sheet.')
    parser.add_argument('timesheet',
                        nargs='*',
                        help='path to time sheet file')
    parser.add_argument('-r', '--resolution',
                        nargs='*',
                        choices=[t[0] for t in TRUNC_DATE],
                        )
    parser.add_argument('-l', '--level', type=int, default=1)
    parser.add_argument('--since', type=date_type)
    # parser.add_argument('-n', '--notes', dest='notes', action='store_true',
    #                     help="show notes output in summary")
    parser.add_argument('-c', '--commits', action='store_true',
                        help="show commits to repo")
    # parser.add_argument('--afk', dest='afk', action='store_true',
    #                     help="include time spent AFK")
    args = parser.parse_args()
    main()
