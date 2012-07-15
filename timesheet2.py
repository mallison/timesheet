import argparse
import itertools
import os
import re
import sys
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from operator import itemgetter

# TODO git integration
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
                       task,
                       note,
                       )


def validate(slots):
    # TODO some validation!!
    prev_slot = None
    day_start_slot = None
    for slot in slots:
        if not slot.end > slot.start:
            print >>sys.stderr, "invalid"
        if prev_slot == None:
            prev_slot = day_start_slot = slot
        if slot.start.day != prev_slot.start.day:
            if not (slot.start.day == prev_slot.start.day + 1):  # TODO not correct!
                print >>sys.stderr, "days out of sequence"
                print >>sys.stderr, (prev_slot, slot)
            length_of_day = prev_slot.end - day_start_slot.start
            if length_of_day < timedelta(hours=8):  # TODO doesn't account for AFK!
                print >>sys.stderr, "short day %s" % (prev_slot,)
            day_start_slot = slot
        prev_slot = slot
        if slot.task.lower() not in AFK:  # TODO make afk filter optional
            if slot.task == '':
                slot = Slot(slot.start, slot.end, "misc", slot.note)
            yield slot


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
    for slot in slots:
        duration = slot.end - slot.start
        totals[slot.task] += duration
        overall += duration
    most = max([t[1] for t in totals.items()])
    for task, total in sorted(totals.items(), key=itemgetter(1)):
        print "{:20s} {:15s} {}".format(
            task,
            man_days(total),
            "#" * int(50 * total.total_seconds() / most.total_seconds())
            )
    print "{:20s} {}".format("OVERALL", man_days(overall))


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
    for path in args.timesheet:
        with open(path) as f:
            slots.extend(parse_file(f))
    show_groups(since(slots), args.resolution)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a time sheet.')
    parser.add_argument('timesheet',
                        nargs='+',
                        help='path to time sheet file')
    parser.add_argument('-r', '--resolution',
                        nargs='*',
                        choices=[t[0] for t in TRUNC_DATE],
                        )
    parser.add_argument('--since', type=date_type)
    # parser.add_argument('-n', '--notes', dest='notes', action='store_true',
    #                     help="show notes output in summary")
    # parser.add_argument('-r', '--repo',
    #                     help="show commits to repo")
    # parser.add_argument('--afk', dest='afk', action='store_true',
    #                     help="include time spent AFK")
    args = parser.parse_args()
    main()
