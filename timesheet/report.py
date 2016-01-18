import itertools
from datetime import datetime

AFK = ['lunch', 'afk']

def report(slots, granularity, max_depth=1, indent=0):
    time_unit = granularity[0]
    key_func = _get_key_func(time_unit)
    for period, slots_in_period in itertools.groupby(slots, key_func):
        period_summary = {}
        slots_in_period = list(slots_in_period)
        for slot in slots_in_period:
            task = slot[1]
            if task[0] in AFK:
                continue
            level = period_summary
            levels = ['main'] + task[:max_depth]
            for subtask in levels:
                if not subtask:
                    subtask = 'misc'
                level.setdefault(subtask, {
                    'duration': 0,
                    'subtasks': {},
                })
                level[subtask]['duration'] += slot[2]
                level = level[subtask]['subtasks']
        print_task(period, period_summary['main'], indent=indent)
        print
        if len(granularity) > 1:
            report(slots_in_period, granularity[1:], max_depth, indent +  4)


def _get_key_func(granularity):
    if granularity == 'day':
        return lambda slot: slot[0].date().strftime('%a %d %b')
    if granularity == 'week':
        return lambda slot: '%s WW%s' % slot[0].date().isocalendar()[:2]
    if granularity == 'month':
        return lambda slot: slot[0].date().strftime('%b %Y')
    if granularity == 'year':
        return lambda slot: str(slot[0].date().year)
    raise ValueError("Granularity '%s' is not valid" % granularity)


def print_task(name, data, top=True, indent=0):
    # if indent > 2:
    name, data = collapse_tasks(name, data)
    # from pprint import pprint
    # pprint(data)
    rows = [
        [
            indent,
            name,
            minutes_as_man_days(data['duration'])
        ]
    ]
    sub_tasks = data['subtasks'].items()
    sub_tasks.sort(key=lambda sub: sub[1]['duration'], reverse=True)
    for task, data in sub_tasks:
        rows.extend(print_task(task, data, False, indent + 2))
    if top:
        tabulate(rows)
    return rows


def collapse_tasks(name, data):
    # if a parent and subtask take the same time collapse to one line
    if len(data['subtasks'].keys()) == 1:
        sub_task = data['subtasks'].keys()[0]
        if data['duration'] == data['subtasks'][sub_task]['duration']:
            # _name, data = collapse_tasks(sub_task, data['subtasks'][sub_task])
            # name += ': ' + _name
            collapse_tasks(sub_task, data['subtasks'][sub_task])
            data['duration'] = 0
    return name, data


def tabulate(rows):
    # max_width = max(len(r[1]) + r[0] for r in rows)
    max_width = 80
    for indent, task, duration in rows:
        # if indent < 4:
        #     print
        formatted_duration = ''
        for amount, unit in zip(duration, 'dhm'):
            if amount:
                formatted_duration += '{:>3}{}'.format(amount, unit)
            else:
                formatted_duration += '    '
        # formatted_duration = '{:.>10}'.format(formatted_duration.strip())
        if sum(duration):
            fill = '.'
        else:
            fill = ' '
        print '{:{fill}<{max_width}}{}'.format(
            (' ' * indent + task), formatted_duration, fill=fill, max_width=max_width)


def minutes_as_man_days(minutes):
    days, minutes = divmod(minutes, 7 * 60)
    hours, minutes = divmod(minutes, 60)
    return days, hours, minutes
