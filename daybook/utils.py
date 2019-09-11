import datetime


def get_current_date():
    return datetime.datetime.now().strftime("%m_%d_%Y")