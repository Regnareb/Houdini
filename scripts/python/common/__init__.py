import sys
import logging
import pathlib
import importlib
from PySide6 import QtCore

logger = logging.getLogger(__name__)


def __reload_pythonlibs(path):
    name = path.replace('.py', '').replace('/', '.').replace('\\', '.').replace('.__init__', '')
    name = name.split('python.')[-1]
    try:
        importlib.reload(sys.modules[name])
        logger.debug("Reloading python module " + name)
    except KeyError:
        logger.warning("Couldn't find the module " + name)


current_dir = pathlib.Path(__file__).parents[1]
files = current_dir.glob('**/*.py')
fs_watcher = QtCore.QFileSystemWatcher()
for f in files:
    fs_watcher.addPath(str(f))
fs_watcher.fileChanged.connect(__reload_pythonlibs)
