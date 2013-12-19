import itertools
import re
import subprocess
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
REFLOG_RE = re.compile(r'^[0-9a-f]+ .*?\{([\d\-: ]+) \+.*?: (.*)$')


class TaskLevelDict(defaultdict):
    """TODO"""
    def __init__(self):
        super(TaskLevelDict, self).__init__(self.__class__)
        self._total = timedelta(0)

    def cumulative_total(self):
        total = self._total
        for sub_level in self.values():
            total += sub_level.cumulative_total()
        return total

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        self._total += value


def group_slots_by_time_period(slots, resolution):
    """Group slots by year, month or day.

    Returns a mapping of the form:

    grouped[<datetime>] = [<slot>, <slot>, ...]

    """
    return itertools.groupby(
        slots,
        lambda slot: TRUNCATE_DATE[resolution](slot['start']))


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
    totals = TaskLevelDict()
    slots = list(slots)
    for slot in slots:
        if slot['task'][0] not in AFK:
            duration = slot['end'] - slot['start']
            sub_level = totals
            for i, part in enumerate(slot['task']):
                sub_level = sub_level[part]
            sub_level.total = duration
    print man_days(totals.cumulative_total())
    _summarize_level(totals, max_level=task_level - 1)
    # most = max([t[1] for t in totals.items()])
    # for task, total in sorted(totals.items(), key=itemgetter(1), reverse=True):
    #     print "{:30s} {:15s} {}".format(
    #         ': '.join(task)[:30],
    #         man_days(total),
    #         "#" * int(50 * total.total_seconds() / most.total_seconds())
    #         )
    #     if show_commits:
    #         for slot in slots:
    #             if slot['task'][:task_level] == task:
    #                 print_commits(slot)
    #         print
    # print "{:30s} {}".format("OVERALL", man_days(overall))


def _summarize_level(level_dict, level=0, max_level=0):
    as_list = [(v.cumulative_total(), v.total, k)
               for k, v in level_dict.items()]
    as_list.sort(reverse=True)
    for cumulative_duration, level_duration, name in as_list:
        label = (' ' * level * 2) + name
        print '%-40s  %s' % (label, man_days(cumulative_duration))
        next_level = level + 1
        if next_level <= max_level:
            if level_duration and level_duration != cumulative_duration:
                label = (' ' * (level + 1) * 2)
                print '%-40s  %s' % (label, man_days(level_duration))
            _summarize_level(level_dict[name],
                             level=level + 1,
                             max_level=max_level)


_commits = None
def print_commits(slot):
    global _commits
    if _commits is None:
        reflog = subprocess.check_output(
            ['git', 'reflog', '--date', 'iso', '--all'])
        _commits = reflog
    for line in  _commits.splitlines():
        m = REFLOG_RE.match(line)
        if m:
            timestamp = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
            if slot['start'] <= timestamp < slot['end']:
                print "    {0:%H%M} {1:}".format(timestamp, m.group(2))


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
