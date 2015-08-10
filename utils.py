from datetime import datetime


def print_task(name, data, indent=0):
    if indent > 2:
        name, data = collapse_tasks(name, data)
    rows = [
        [
            indent,
            name,
            minutes_as_man_days(data['total'])
        ]
    ]
    sub_tasks = data['sub'].items()
    sub_tasks.sort(key=lambda sub: sub[1]['total'], reverse=True)
    for task, data in sub_tasks:
        rows.extend(print_task(task, data, indent + 2))
    if indent == 0:
        tabulate(rows)
    return rows


def collapse_tasks(name, data):
    # if a parent and subtask take the same time collapse to one line
    if len(data['sub'].keys()) == 1:
        sub_task = data['sub'].keys()[0]
        if data['total'] == data['sub'][sub_task]['total']:
            _name, data = collapse_tasks(sub_task, data['sub'][sub_task])
            name += ': ' + _name
    return name, data


def tabulate(rows):
    max_width = max(len(r[1]) + r[0] for r in rows)
    for indent, task, duration in rows:
        if indent <= 4:
            print
        formatted_duration = ''
        for amount, unit in zip(duration, 'dhm'):
            if amount:
                formatted_duration += '{:>3}{}'.format(amount, unit)
            else:
                formatted_duration += '    '
        print '{:.<{max_width}}{}'.format(
            (' ' * indent + task), formatted_duration, max_width=max_width)


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
