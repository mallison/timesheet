from impl import *


def _handle_line(line):
    day = get_day(line)
    try:
        timestamp, task = get_timestamp_and_task(line)
    except AttributeError:
        timestamp = None

    if day:
        # validate_day()
        close_current_day()
        set_datetime_to_this_day(day)

    elif timestamp:
        # validate_task_name(task)
        # validate_task_start(timestamp)
        if is_last_task_open():
            # validate_task_close_time
            close_last_task(timestamp)
        start_task(timestamp, task)

    elif is_end_of_timesheet(line):
        close_current_day()
        return

    else:
        if is_last_task_open():
            add_line_to_task_notes(line)
        # else:
        #     warn_about_stray_text


if __name__ == '__main__':
    main(_handle_line)
