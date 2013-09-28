from datetime import date, datetime, timedelta


def from_(timesheet, from_datetime):
    return (chunk for chunk in timesheet if chunk['end'] >= from_datetime)


def to(timesheet, to_datetime):
    return (chunk for chunk in timesheet if chunk['end'] < to_datetime)


def task(timesheet, task):
    depth = len(task)
    return (chunk for chunk in timesheet
            if chunk['task'][:depth] == task[:depth])


def stand_up(timesheet):
    # TODO account for Monday and Friday
    # TODO slicker way to get start of day as datetime?
    today = date.today()
    today = datetime(today.year, today.month, today.day)
    start = today - timedelta(1)
    end = start + timedelta(2)
    return from_(to(timesheet, end), start)
