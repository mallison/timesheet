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
    # TODO slicker way to get start of day as datetime?
    today = date.today()
    weekday = today.weekday()
    if weekday >= 5:
        today += timedelta(days=4 - weekday)
    today = datetime(today.year, today.month, today.day)
    if weekday == 0:
        start = today - timedelta(3)
        end = start + timedelta(4)
    else:
        start = today - timedelta(1)
        end = start + timedelta(2)
    return from_(to(timesheet, end), start)
