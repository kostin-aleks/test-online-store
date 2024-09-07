from math import ceil, sqrt
import string
import random


def random_string_alphadigit(count):
    """
    return random string that contains digits and lowercase chars
    """
    # using random.choices()
    # generating random strings
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=count))


def mean_value(data):
    """ average value of list """
    cnt = len(data)
    if not cnt:
        return None

    return sum(data) / cnt


def rms(data):
    """
    root mean square
    """
    cnt = len(data)
    mean = mean_value(data)
    if mean is None:
        return None
    diff_summ = sum([(x - mean) ** 2 for x in data])

    return sqrt(diff_summ / cnt)


def get_gender(value):
    """
    get gender from string or int
    """
    if isinstance(value, str):
        value = value.lower()[:1]
        if value in ['m', '0']:
            return 0
        if value in ['f', '1']:
            return 1
        return None
    if isinstance(value, int):
        return value
    return None


def atoi(variable, default=None):
    """
    get int of variable
    """
    if isinstance(variable, str) and len(variable):
        s = ''
        i = 0
        while i < len(variable) and variable[i].isdigit():
            print(i, variable[i])
            s = s + variable[i]
            i += 1
        variable = s

    try:
        variable = int(variable)
    except ValueError:
        try:
            variable = float(variable)
            variable = int(variable)
        except ValueError:
            variable = default
    except TypeError:
        variable = default
    return variable
