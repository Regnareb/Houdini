
"""Directly open image sequences with mplay by double clicking on any image
Python path needs to be in your environment variables

Window: Right click on a file > Open With and find the open_with_mplay.bat
"""

import os
import re
import sys
sys.path.append(os.path.join(os.path.abspath(__file__), 'python3.9libs'))
import lib.pythonlib.iopath


def get_binary_path(path, pattern):
    folderpath = sorted([i.path for i in os.scandir(path) if i.is_dir() and re.search(pattern, i.name)])[-1]
    folderpath = os.path.join(folderpath, 'bin')
    return folderpath


if __name__ == "__main__":
    filepath = sys.argv[1]
    _, filepath = lib.pythonlib.iopath.get_file_sequence(filepath, '$F')

    if sys.platform.startswith('darwin'):
        folder_binary = get_binary_path('/Applications/Houdini/', 'Houdini')
    elif sys.platform.startswith('linux'):
        folder_binary = get_binary_path('/opt/', 'hfs')
    elif sys.platform.startswith('win32'):
        folder_binary = get_binary_path('C:/Program Files/Side Effects Software/', 'Houdini \\d')

    assert os.path.isdir(folder_binary)
    os.chdir(folder_binary)
    os.system('mplay -p -P loop ' + filepath)
