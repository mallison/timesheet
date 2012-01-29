"""Simple timesheet text file tools.

Produce reports from timesheets stored in a simple text file format.

>>> from StringIO import StringIO
>>> example = StringIO('''
... Monday
... 0900
...
... 0930 Admin
... - respond to various emails on stuff
... - updated last weeks timesheets!
...
... 1000 www
... - tweaks to site home page
... - calendar widget added for event lookup
...
... 1300 Lunch
...
... 1400 www
... - finished calendar javascript
...
... 1730
... ''')

# In usual usage timesheet files will be read from disk.  Timesheet
# assumes the name of the file gives the date so we add a name
# attribute to our example buffer
>>> example.name = '20110404.txt'

>>> t = Timesheet(example)

# The Timesheet class exposes one method to generate a weekly summary
# of time spent on tasks

>>> t.week_summary()
Monday
------
0:30:00: Admin
- respond to various emails on stuff
- updated last weeks timesheets!
<BLANKLINE>
1:00:00: Lunch
<BLANKLINE>
0:30:00: Miscellaneous
<BLANKLINE>
6:30:00: www
- tweaks to site home page
- calendar widget added for event lookup
<BLANKLINE>
- finished calendar javascript
<BLANKLINE>
TOTAL TIME: 7:30:00

"""

# TODO: special notation for public holidays and leave
# TODO: integrity check on days and week
#       - suspiciously low or high hours in a day
#       - missing days in a week

import datetime
import os
import re
from optparse import OptionParser


class TimesheetError(Exception):
    """Base class for errors in the timesheet module"""
    pass


class Timesheet(object):
    _DAYS = [datetime.date(2008, 9, _x).strftime('%A') for _x in range(1, 8)]
    _TASK_START_REGEXP = re.compile(r'^(\d{4})([ \w\/\.]*)$')
    _UNASSIGNED_TASK = 'Miscellaneous'
    _NON_WORKING = ['tea', 'lunch', 'afk']

    def __init__(self, timesheet):
        self.current_day = None
        self.timesheet = timesheet
        self._set_start_date()
        self.tasks = {}
        self._parse()

    def _current_task(self):
        if (not self.tasks or
            not self.tasks[self.current_day] or
            'end' in self.tasks[self.current_day][-1]):
            return None
        return self.tasks[self.current_day][-1]

    def _set_start_date(self):
        try:
            filename = os.path.splitext(
                os.path.basename(self.timesheet.name))[0]
            self.start_date = datetime.datetime(int(filename[:4]),
                                                int(filename[4:6]),
                                                int(filename[6:]))
        except (AttributeError, IndexError):
            raise TimesheetError("Timesheet file is not named correctly")
        if not self.start_date.weekday() == 0:
            raise TimesheetError("Timesheet date is not a Monday")

    def _parse_task_start(self, m):
        if self.current_day is None:
            raise TimesheetError("You can't have tasks outside of a day!")
        hours, minutes = int(m.group(1)[:2]), int(m.group(1)[2:4])
        start_time = self.current_day + datetime.timedelta(hours=hours,
                                                           minutes=minutes)
        if not start_time.day == self.current_day.day:
            raise TimesheetError("Invalid time %s%s" % (hours, minutes))
        task_name = m.group(2).strip()
        if not task_name:
            task_name = self._UNASSIGNED_TASK
        return task_name, start_time

    def _start_task(self, task_name, start_time):
        # end the previous task if appropriate
        if self._current_task() is not None:
            self._end_task(start_time)
        todays_tasks = self.tasks[self.current_day]
        todays_tasks.append({'name': task_name,
                             'start': start_time,
                             'notes': []})

    def _end_task(self, end_time):
        todays_tasks = self.tasks[self.current_day]
        if end_time <= todays_tasks[-1]['start']:
            raise TimesheetError(
                "Task %s cannot end in the past %s" %
                (self._current_task()['name'], todays_tasks[-1]['start']))
        todays_tasks[-1]['end'] = end_time

    def _add_note(self, note):
        if not self._current_task():
            if note.strip():
                raise TimesheetError("Cannot have note here: %s" % note)
            return
        self.tasks[self.current_day][-1]['notes'].append(note)

    def _start_day(self, day):
        day = self._DAYS.index(day)
        if self.current_day is None and day != 0:
            # Monday expected as the first day
            raise TimesheetError("Monday has to be the first day")
        if day > 0 and  day != self.current_day.weekday() + 1:
            # Days out of sequence
            raise TimesheetError(
                "Expected %s after %s but got %s instead (%s)" % (
                    (self.current_day +
                     datetime.timedelta(days=1)).strftime('%A'),
                    self.current_day.strftime('%A'),
                    self._DAYS[day],
                    self.timesheet.name))
        # end the previous day if appropriate
        if self.current_day is not None:
            self._end_day()
        self.current_day = self.start_date + datetime.timedelta(days=day)
        self.tasks[self.current_day] = []

    def _end_day(self):
        if not self.tasks[self.current_day]:
            raise TimesheetError(
                "No tasks found in %s" % self.current_day.strftime('%A %d %b'))
        # anything other than a noteless, taskless last 'task' means that
        # the real last task has not been properly closed (one task is a
        # special case because a properly closed day will have at least two
        # tasks)
        todays_tasks = self.tasks[self.current_day]
        if (len(todays_tasks) == 1 or
            todays_tasks[-1]['name'] != self._UNASSIGNED_TASK or
            ''.join(todays_tasks[-1]['notes']).strip()):
            # no end time given for the last task of the current day
            raise TimesheetError(
                "No end time given for task %s on %s" % (
                    self._current_task()['name'],
                    self.current_day.strftime('%A %d %b')))
        # an end time on a day will have created a false unassigned
        # task that we need to remove (the last real task will have
        # been closed)
        del(self.tasks[self.current_day][-1])
        self.current_day = None

    def _parse(self):
        for line in self.timesheet.readlines():
            if (line.startswith('-' * 20) or
                line.startswith('#' * 20) or
                line.startswith('STACK') or
                line.startswith('***')):
                # Notes are placed at the end of the timesheet after a line
                # of 20 or more '-'s
                break
            line = line.strip()
            if line in self._DAYS:
                self._start_day(line)
                continue
            m = self._TASK_START_REGEXP.search(line)
            if m:
                task_name, start_time = self._parse_task_start(m)
                self._start_task(task_name, start_time)
                continue
            self._add_note(line)

        # End the last day
        if self.current_day is None:
            # must have found no days!
            raise TimesheetError("No days found")
        self._end_day()

    def week_summary(self):
        days = self.tasks.keys()
        days.sort()
        weeks_tasks = []
        for day in days:
            day_name = day.strftime('%A')
            print day_name
            print '-' * len(day_name)
            self._aggregate_timeslots(self.tasks[day])
            weeks_tasks.extend(self.tasks[day])
        print '\nWeek'
        print '----'
        self._aggregate_timeslots(weeks_tasks)

    def _aggregate_timeslots(self, timeslots):
        by_task = {}
        for timeslot in timeslots:
            by_task.setdefault(timeslot['name'], []).append(timeslot)
        tasks = by_task.keys()
        tasks.sort(lambda a, b: cmp(a.lower(), b.lower()))
        total_time = datetime.timedelta(0)
        for task in tasks:
            task_time = sum([x['end'] - x['start'] for x in by_task[task]],
                            datetime.timedelta(0))
            if not task.lower() in self._NON_WORKING:
                total_time += task_time
            print '%s: %s' % (task_time, task)
            for timeslot in by_task[task]:
                print '\n'.join(timeslot['notes'])
        print 'TOTAL TIME: %s' % total_time


def main():
    parser = OptionParser(usage="%prog timesheet_file [OPTIONS]")
    parser.add_option('--test', default=False, dest="test",
                      action="store_true",
                      help="Run module tests")
    options, args = parser.parse_args()
    if not options.test:
        if len(args) != 1:
            parser.error("Please specify a timesheet file to parse")
        timesheet = Timesheet(open(args[0]))
        timesheet.week_summary()
    else:
        import doctest
        doctest.testmod()

if __name__ == '__main__':
    main()
