import re
from datetime import datetime, timedelta


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
            time, task = m.groups()
            task = tuple(t.strip() for t in task.split(':'))
            return time, task
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
