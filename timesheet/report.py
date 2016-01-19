import itertools

AFK = ['lunch', 'afk']

def report(slots, granularity, max_depth=1, indent=0):
    time_unit = granularity[0]
    key_func = _get_key_func(time_unit)
    for period, slots_in_period in itertools.groupby(slots, key_func):
        slots_in_period = list(slots_in_period)
        task_summary = _get_task_durations_for_period(
            slots_in_period,
            max_depth
        )
        _print_task_summary(period, task_summary, indent=indent)
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


def _get_task_durations_for_period(slots_in_period, max_depth):
    task_summary = {}
    for slot in slots_in_period:
        task = slot.task
        if task[0] in AFK:
            continue
        level = task_summary
        levels = ['main'] + task[:max_depth]
        for subtask in levels:
            if not subtask:
                subtask = 'misc'
            level.setdefault(subtask, {
                'duration': 0,
                'subtasks': {},
            })
            level[subtask]['duration'] += slot.duration
            level = level[subtask]['subtasks']
    return task_summary['main']


def _print_task_summary(name, data, top=True, indent=0):
    _collapse_tasks(data)
    rows = [
        [
            indent,
            name,
            _minutes_as_man_days(data['duration'])
        ]
    ]
    subtasks = data['subtasks'].items()
    subtasks.sort(key=lambda sub: sub[1]['duration'], reverse=True)
    for task, data in subtasks:
        rows.extend(_print_task_summary(task, data, False, indent + 2))
    if top:
        _tabulate(rows)
    return rows


def _collapse_tasks(data):
    # if a parent and subtask take the same time only show duration for
    # subtask
    if len(data['subtasks'].keys()) == 1:
        subtask = data['subtasks'].keys()[0]
        if data['duration'] == data['subtasks'][subtask]['duration']:
            _collapse_tasks(data['subtasks'][subtask])
            data['duration'] = 0


def _tabulate(rows):
    # max_width = max(len(r[1]) + r[0] for r in rows)
    max_width = 80
    for indent, task, duration in rows:
        formatted_duration = ''
        for amount, unit in zip(duration, 'dhm'):
            if amount:
                formatted_duration += '{:>3}{}'.format(amount, unit)
            else:
                formatted_duration += '    '
        if sum(duration):
            fill = '.'
        else:
            fill = ' '
        print '{:{fill}<{max_width}}{}'.format(
            (' ' * indent + task), formatted_duration, fill=fill, max_width=max_width)


def _minutes_as_man_days(minutes):
    days, minutes = divmod(minutes, 7 * 60)
    hours, minutes = divmod(minutes, 60)
    return days, hours, minutes
