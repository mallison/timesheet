import itertools
import os
import pickle
import re
from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter

MAN_DAY = 7.0  # hours
AFK = ['afk', 'tea', 'lunch']
TRUNCATE_DATE = {
    'year': lambda d: datetime(d.year, 1, 1),
    'month': lambda d: datetime(d.year, d.month, 1),
    'day': lambda d: datetime(d.year, d.month, d.day),
}
DATE_FORMAT = {
    'year': "%Y",
    'month': "%b %Y",
    'day': "%a %b %d, %Y",
}
COMMIT_LOG = os.path.expanduser('~/.gitlog')


def group_slots_by_time_period(slots, resolution):
    """Group slots by year, month or day.

    Returns a mapping of the form:

    grouped[<datetime>] = [<slot>, <slot>, ...]

    """
    return itertools.groupby(
        slots,
        lambda slot: TRUNCATE_DATE[resolution](slot.start))


def show_groups(slots, resolutions=None, task_level=1, show_commits=False):
    for resolution in resolutions or [None]:
        date_format = DATE_FORMAT.get(resolution)
        if resolution is not None:
            grouped = group_slots_by_time_period(slots, resolution)
        else:
            grouped = ('All', slots),
        for date, slots in grouped:
            print
            print '-' * 72
            print date_format and date.strftime(date_format) or date
            summarize(slots, task_level=task_level, show_commits=show_commits)


def summarize(slots, task_level=1, show_commits=False):
    totals = defaultdict(lambda: timedelta(0))
    overall = timedelta(0)
    slots = list(slots)
    for slot in slots:
        if slot['task'][0] not in AFK:
            duration = slot['end'] - slot['start']
            totals[slot['task'][:task_level]] += duration
            overall += duration
    most = max([t[1] for t in totals.items()])
    for task, total in sorted(totals.items(), key=itemgetter(1)):
        print "{:30s} {:15s} {}".format(
            ': '.join(task)[:30],
            man_days(total),
            "#" * int(50 * total.total_seconds() / most.total_seconds())
            )
        if show_commits:
            for slot in slots:
                if slot.task[:task_level] == task:
                    print_commits(slot)
            print
    print "{:30s} {}".format("OVERALL", man_days(overall))


_commits = None
def print_commits(slot):
    global _commits
    if _commits is None:
        with open(COMMIT_LOG) as f:
            _commits = pickle.load(f)
    commits = [c for c in _commits if slot.start <= c[0] < slot.end]
    for time, msg in commits:
        msg = re.sub(r'^#.*$', '', msg, flags=re.M).strip()
        print "    {0:%H%M} {1:}".format(time, msg)


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
    # days, minutes = divmod(minutes, MAN_DAY * 60)
    hours, minutes = divmod(minutes, 60)
    out = []
    for measure, amount in zip(("h", "m"),
                               (hours, minutes)):
        if amount:
            out.append("{:.0f}{}".format(amount, measure))
    return " ".join(out)
