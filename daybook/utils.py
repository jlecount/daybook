import os
import re
import datetime


def get_entry_filename(project_dir, timestamp:float, is_encrypted:bool):
    """
    Construct a filename for a given timestamp, encrypted or not
    :param timestamp: the time, via time.time()
    :param is_encrypted: the time, via time.time()
    """
    extension = ".txt.encrypted" if is_encrypted else ".txt"
    return os.path.join(project_dir, get_current_date(), str(timestamp) + extension)

def sort_filename_by_date(fn:str):
    """
    Returns a sort key usable by the sorted() builtin
    :param fn: the filename in the format <dir>/mm_dd_yyyy/<timestamp>.<micro>.txt
    """
    return int(re.sub(r'.*/(\d\d)_(\d\d)_(\d\d\d\d)/(\d+)\..*', '\\3\\1\\2\\4', fn))

def str_to_bool(v:str) -> bool:
    """
    Given a string value v, return the boolean representation of it
    :param v: a string either "True" or "False".  None is allowed and will be returned unchanged.
    :return: a boolean value corresponding to the string input.
    :raises: Exception if the input is not "True", "False" or None
    """
    if v is None:
        return v
    elif type(v) is bool:
        return v
    else:
        if v not in ["False", "True"]:
            raise Exception("Invalid input: {}".format(v))
        else:
            return eval(v)


def get_current_date():
    return datetime.datetime.now().strftime("%m_%d_%Y")
