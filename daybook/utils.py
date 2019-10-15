import datetime


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