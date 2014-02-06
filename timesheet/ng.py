for line in timesheet:
    if line_starts_day or line_is_note_separator:
        if exists_open_task:
            remove_open_task
        if line_starts_day:
            validate_day
            set_time_to_this_day
        else:
            break
    elif line_starts_task:
        validate_task_name
        validate_task_start
        if exists_open_task:
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

