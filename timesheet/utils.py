import datetime
import os


FILE_NAME_DATE_FORMAT = "%Y%m%d"


def start_date_from_file_name(file_name):
    return datetime.datetime.strptime(
        os.path.splitext(os.path.basename(file_name))[0],
        FILE_NAME_DATE_FORMAT)
