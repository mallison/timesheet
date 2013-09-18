# AGAIN!?, REALLY!?
import re
from datetime import datetime, timedelta

class Timesheet(object):
    days = [datetime(2013, 9, d).strftime('%A') for d in range(16, 23)]
    timestamp_regexp = re.compile(r'^(\d{4})(?:\s+(.*))?$')

    def __init__(self, file_like):
        self.when = datetime(2013, 9, 18)
        self._chunks = []
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
        time = self.when + timedelta(hours=int(time[:2]), minutes=int(time[2:]))
        if len(self._chunks):
            self._chunks[-1]['end'] = time
        self._chunks.append(dict(task=task, start=time))

    def _close_last_chunk(self):
        if len(self._chunks) > 1:
            close_time = self._chunks[-1]['start']
            del self._chunks[-1]
            self._chunks[-1]['end'] = close_time


if __name__ == '__main__':
    import sys
    from pprint import pprint
    timesheet = Timesheet(open(sys.argv[1]))
    pprint(timesheet._chunks)
