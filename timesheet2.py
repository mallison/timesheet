import os
import re
from collections import OrderedDict, defaultdict, namedtuple
from datetime import datetime, timedelta
from operator import itemgetter

# TODO git integration
# TODO bug tracker integration
# TODO command line options for which grouping to show

SLOT_REGEXP = re.compile(
    r"""
    (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*
    (\d{4})\ ?(.*?)\n
    (.*?)
    (?=\n(\d{4})|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)
    """, re.DOTALL | re.X)
AFK = ['afk', 'tea', 'lunch']
TRUNC_DATE = (
    ('all', lambda d: None, ""),
    ('year', lambda d: datetime(d.year, 1, 1), "%Y"),
    ('month', lambda d: datetime(d.year, d.month, 1), "%b %Y"),
    # TODO ('week', lambda d: datetime(????), "%U %Y"),
    ('day', lambda d: datetime(d.year, d.month, d.day), "%a %b %d, %Y")
)
MAN_DAY = 7.5  # hours
NOTES_DELIMITER = '-' * 50

Slot = namedtuple('Slot', "day start end task note")


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
    Convert day and start and end times to datetime objects.
    """
    for day, start, task, note, end in slots:
        if day and day != "Monday":
            start_date += timedelta(days=1)
        if end:  # TODO fix regexp to not grab end of day as a task!
            yield Slot(start_date,
                       start_date + to_timedelta(start),
                       start_date + to_timedelta(end),
                       task,
                       note,
                       )


def validate(slots):
    # TODO some validation!!
    for slot in slots:
        if slot.task.lower() not in AFK:
            yield slot


def group(slots):
    groups = {}
    for slot in slots:
        for time_period, date_trunc_func, time_period_format in TRUNC_DATE:
            (groups
             .setdefault(time_period, OrderedDict())
             .setdefault(date_trunc_func(slot.day), [])
             .append(slot))
    return groups


def show_groups(groups):
    for time_period, date_trunc_func, time_period_format in TRUNC_DATE:
        for date, slots in groups[time_period].items():
            print
            if date:
                print date.strftime(time_period_format)
            else:
                print 'All'
            summarize(slots)


def summarize(slots):
    totals = defaultdict(lambda: timedelta(0))
    overall = timedelta(0)
    for slot in slots:
        duration = slot.end - slot.start
        totals[slot.task] += duration
        overall += duration
    for task, total in sorted(totals.items(), key=itemgetter(1)):
        print "{:20s} {}".format(task, man_days(total))
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
    for measure, amount in zip(("day", "hour", "minute"),
                               (days, hours, minutes)):
        if amount:
            out.append("{:.0f} {}{}".format(
                    amount, measure, "s" if amount > 1 else ""))
    return ", ".join(out)

if __name__ == '__main__':
    import sys
    show_groups(group(parse_file(open(sys.argv[1]))))
