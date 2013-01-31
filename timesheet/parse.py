from collections import namedtuple
import datetime
import re

# TODO validation!

MISC_TASK = 'misc'
DAYS = [datetime.date(2013, 1, 21 + s).strftime('%A') for s in range(7)]
TASK_START_RE = re.compile(r'^\d{4}')
NOTES_DELIMITER = '-' * 50

Slot = namedtuple('Slot', "start end task note")


def parse(file_like, start_datetime):
    day = start_datetime
    slots = []
    for line in file_like:
        if line.strip().startswith(NOTES_DELIMITER):
            break
        elif line.rstrip() in DAYS:
            day = get_new_day(slots, day, line.rstrip())
        elif TASK_START_RE.search(line):
            add_new_slot(slots, day, line.rstrip())
        else:
            add_line_to_current_slot_note(slots, line)
    del slots[-1]  # TODO explain this!
    return slots


def get_new_day(slots, day, line):
    if slots:
        previous_day = slots[-1].start.strftime('%A')
        day += datetime.timedelta(
            DAYS.index(line) - DAYS.index(previous_day))
        del slots[-1]  # TODO explain this!
    else:
        day += datetime.timedelta(DAYS.index(line))
    return day


def add_new_slot(slots, day, line):
    try:
        time, task = line.split(' ', 1)
    except ValueError:
        time = line
        task = MISC_TASK
    task = parse_hierarchical_tasks(task)
    time = to_timedelta(time)
    time = day + time
    if slots:
        previous_slot = slots[-1]
        if previous_slot.end is None:  # TODO explain this!
            slots[-1] = Slot(previous_slot.start,
                             time,
                             previous_slot.task,
                             previous_slot.note)
    slots.append(Slot(time, None, task, []))


def add_line_to_current_slot_note(slots, line):
    slots[-1].note.append(line)


def parse_hierarchical_tasks(task):
    return tuple((t.strip() for t in task.split(':')))


def to_timedelta(time_string):
    """Convert a string in HHMM format to a timedelta.

    >>> to_timedelta("0832")
    datetime.timedelta(0, 30720)
    """
    return datetime.timedelta(seconds=seconds(time_string))


def seconds(time_string):
    """Convert a string in HHMM format to a number of seconds.

    >>> seconds("1341")
    49260
    """
    return 60 * (int(time_string[:2]) * 60 + int(time_string[2:]))
