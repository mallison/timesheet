"""Timesheet parsing functional stylee!"""
import re
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
from pprint import pprint

TRUNC_DATE = (
    ('all', lambda d: None, ""),
    ('year', lambda d: datetime(d.year, 1, 1), "%Y"),
    ('month', lambda d: datetime(d.year, d.month, 1), "%b %Y"),
    ('day', lambda d: datetime(d.year, d.month, d.day), "%a %b %d, %Y")
)

START = datetime(2012, 2, 27)


def parse(file):
    weekly = re.compile(
        r"""
    (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*
    (\d{4})\ ?(.*?)\n
    (.*?)
    (?=(\d{4})|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)
    """, re.DOTALL | re.X)
    return re.finditer(weekly, file.read())


def minutes(time):
    return int(time[:2]) * 60 + int(time[2:])


def to_datetime(day, time):
    return day + timedelta(seconds=minutes(time) * 60)


def duration(slots):
    global START
    for m in slots:
        day, start, task, note, end = m.groups()
        if day:
            START += timedelta(days=1)
        if end:  # TODO fix regexp to not grab end of day as a task!
            start = to_datetime(START, start)
            end = to_datetime(START, end)
            yield START, start, task, note, end, end - start


def task(task, slots):
    for slot in slots:
        if slot[2] == task:
            yield slot


def total(slots):
    return sum((s[-1] for s in slots))


def man_days(delta):
    minutes = delta.seconds / 60
    days, minutes = divmod(minutes, 7.5 * 60)
    hours, minutes = divmod(minutes, 60)
    out = []
    for measure, amount in zip(("day", "hour", "minute"),
                               (days, hours, minutes)):
        if amount:
            out.append(
                "{:.0f} {}{}".format(amount, measure, "s" if amount > 1 else ""))
    return ", ".join(out)


def summarize(slots):
    totals = defaultdict(lambda: timedelta(0))
    for day, start, task, note, end, duration in slots:
        totals[task] += duration
    for task, total in sorted(totals.items(), key=itemgetter(1)):
        print "{:20s} {}".format(task, man_days(total))


def group(slots):
    groups = {}
    for slot in slots:
        for group, func, fmt in TRUNC_DATE:
            groups.setdefault(
                group, OrderedDict()
                ).setdefault(func(slot[0]), []).append(slot)
    for group, func, fmt in TRUNC_DATE:
        for date, slots in groups[group].items():
            print
            if date:
                print date.strftime(fmt)
            else:
                print 'All'
            summarize(slots)


#pprint(list(task('reporting', duration(parse(open(sys.argv[1]))))))
#summarize(duration(parse(open(sys.argv[1]))))
group(duration(parse(open(sys.argv[1]))))
#print man_days(total(task(sys.argv[2], duration(parse(open(sys.argv[1]))))))
