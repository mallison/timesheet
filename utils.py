def minutes_as_man_days(minutes):
    """
    Return ``minutes`` in human readable man days.

    >>> import timedelta
    >>> t = (3 * 7.5 * 60) + (3 * 60) + 1210)
    >>> man_days(t)
    '3 days, 3 hours, 20 minutes'

    """
    days, minutes = divmod(minutes, 7 * 60)
    hours, minutes = divmod(minutes, 60)
    out = []
    for measure, amount in zip(("d", "h", "m"),
                               (days, hours, minutes)):
        if amount:
            out.append("{:.0f}{}".format(amount, measure))
    return " ".join(out)


def hhmm_to_minutes(hhmm):
    return 60 * int(hhmm[:2]) + int(hhmm[2:])
