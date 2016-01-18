from datetime import datetime


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


def hhmm_to_minutes(hhmm):
    if hhmm == '9999':
        hhmm = get_current_time()
    return 60 * int(hhmm[:2]) + int(hhmm[2:])


def get_current_time():
    return datetime.now().strftime('%H%M')
