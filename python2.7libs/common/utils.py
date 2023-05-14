import os
import re
import itertools


def toNumber(s):
    """Convert a string to an int or a float depending of their types"""
    try:
        return int(s)
    except ValueError:
        return float(s)


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in _nsre.split(s)]


def normpath(path):
    """Fix some problems with some file commands needing double escaped anti-slash '\\\\' in the path in Windows"""
    return os.path.normpath(path).replace('\\', '/')


def get_envvar_path(path, envvar):
    """Return the path converted to a path with the environment variable replacing a part of the path if it's possible."""
    path = normpath(path)
    envpath = normpath(os.getenv(envvar))
    path = path.replace(envpath, '${}'.format(envvar))
    return path


def get_relative_path(path, envvar):
    """Convert path to relative path from path in environment variable"""
    path = normpath(path)
    envpath = normpath(os.getenv(envvar))
    return os.path.relpath(path, envpath)


def get_absolute_path(path, envvar):
    """Convert path with environment variable to full absolute path"""
    return path.replace('${}'.format(envvar), os.getenv(envvar))


def parse_strings(filepath, params):
    """Convert all the data to the final one"""
    path = get_envvar_path(filepath, 'HIP')
    path = get_envvar_path(path, 'JOB')
    for i in params:
        try:
            params[i] = params[i].replace('%FILEPATH%', path)
            if '%CONTENT%' in params[i]:
                with open(filepath) as f:
                    params[i] = params[i].replace('%CONTENT%', f.read())
        except AttributeError:
            pass  # If the attribute is not a string
    return params


def get_file_sequence(filepath, prefix='', suffix=''):
    """Detect if the filepath is a single file or a sequence and replace the numbers with"""
    # TODO
    folder, filename = os.path.split(filepath)
    mo = re.findall('\d+', filename)
    mo = list(re.finditer('\d+', filename))
    for i in mo[::-1]:
        num = toNumber(i.group())
        padding = '{{:0>{}}}'.format(len(i.group()))
        decremented = os.path.join(folder, filename[:i.start()] + padding.format(num - 1) + filename[i.end():])
        incremented = os.path.join(folder, filename[:i.start()] + padding.format(num + 1) + filename[i.end():])
        if os.path.exists(decremented) or os.path.exists(incremented):
            return True, os.path.join(folder, filename[:i.start()] + prefix + str(len(i.group())) + suffix + filename[i.end():]).replace('\\', '/')
    return False, filepath


class Enum():
    """An infinite loop between all elements of a list,
    Usefull for having an incremental "toggle"
    """
    def __init__(self, enum_list):
        self.enum_list = itertools.cycle(enum_list)

    def next(self, current=None):
        if current not in self.enum_list:
            return next(self.enum_list)
        for i in self.enum_list:
            if i==current:
                return next(self.enum_list)