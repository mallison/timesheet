import os
import re
import sys
from datetime import date, datetime, timedelta
from pprint import pprint


class Timesheet(list):
    days = [datetime(2013, 9, d).strftime('%A') for d in range(16, 23)]
    timestamp_regexp = re.compile(r'^(\d{4})(?:\s+(.*))?$')

    def __init__(self, start_time, file_like):
        super(Timesheet, self).__init__()
        self.when = start_time
        self._parse(file_like)

    def _parse(self, f):
        for line in f:
            day = self._parse_day(line)
            time, task = self._parse_timestamp(line)

            if day > 0:
                self._new_day(day)

            elif time:
                self._new_chunk(time, task)

            elif '-' * 20 in line:
                break
        self._close_last_chunk()

    def _parse_day(self, line):
        line = line.strip()
        try:
            return self.days.index(line)
        except ValueError:
            return None

    def _parse_timestamp(self, line):
        m = self.timestamp_regexp.match(line)
        if m:
            return m.groups()
        else:
            return None, None

    def _new_day(self, day):
        self._close_last_chunk()
        self.when += timedelta(days=1)

    def _new_chunk(self, time, task):
        time = self.when + timedelta(hours=int(time[:2]),
                                     minutes=int(time[2:]))
        if len(self):
            self[-1]['end'] = time
        self.append(dict(task=task, start=time))

    def _close_last_chunk(self):
        if len(self) > 1:
            close_time = self[-1]['start']
            del self[-1]
            self[-1]['end'] = close_time


def read_files(paths):
    timesheet = None
    for path in paths:
        with open(path) as f:
            new_timesheet = Timesheet(_datetime_from_filename(path), f)
            if timesheet is None:
                timesheet = new_timesheet
            else:
                timesheet.extend(new_timesheet)
    return timesheet


def _datetime_from_filename(path):
    filename = os.path.basename(path)
    return datetime(int(filename[:4]),
                    int(filename[4:6]),
                    int(filename[6:8]))


# TODO move filters to another module
def _from(timesheet, from_datetime):
    return (chunk for chunk in timesheet if chunk['end'] >= from_datetime)


def _to(timesheet, to_datetime):
    return (chunk for chunk in timesheet if chunk['end'] < to_datetime)


def _task(timesheet, task):
    return (chunk for chunk in timesheet if chunk['task'] == task)


def _stand_up(timesheet):
    # TODO account for Monday and Friday
    # TODO slicker way to get start of day as datetime?
    today = date.today()
    today = datetime(today.year, today.month, today.day)
    start = today - timedelta(1)
    end = start + timedelta(2)
    return _from(_to(timesheet, end), start)


if __name__ == '__main__':
    timesheet = read_files(sys.argv[1:])
    pprint(list(_stand_up(timesheet)))
