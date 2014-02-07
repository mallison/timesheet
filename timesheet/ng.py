import datetime
import re

DAYS = [datetime.date(2014, 2, d).strftime('%b') for d in range(3, 11)]
TASK_START_REGEX = re.compile(r'(\d{4})')


class Timesheet(object):
    def __init__(self, timesheets):
        self.tasks = []
        for timesheet in timesheets:
            self._parse(timesheet)

    def _parse(self, timesheet):
        for line in timesheet:
            line_starts_day = self.line_starts_day
            if line_starts_day or self.line_is_note_separator:
                if self.exists_open_task:
                    self.remove_open_task()
                if line_starts_day:
                    self.validate_day()
                    self.set_time_to_this_day()
                else:
                    break
            elif self.line_starts_task:
                self.validate_task_name()
                self.validate_task_start()
                if self.exists_open_task:
                    validate_task_close_time
                    close_open_task
                    if reporting_period_complete:
                        report_period
                start_task
            else:
                if exists_open_task:
                    add_line_to_task_notes
                else:
                    warn_about_stray_text
                    
    @property
    def line_starts_day(self):
        if ' ' in self.line:
            first_word, __ = self.line.split(' ')[0]
            if first_word in DAYS:
                return True
        return False

    @property
    def line_is_note_separator(self):
        return '-' * 50 in self.line

    @property
    def exists_open_task(self):
        return len(self.tasks) > 1 and 'end' not in self.tasks[-1]

    def remove_open_task(self):
        del self.tasks[-1]
        
    def validate_day(self):
        pass

    def set_time_to_this_day(self):
        pass

    @property
    def get_task_start(self):
        m = TASK_START_REGEX.match(self.line)
        if m
