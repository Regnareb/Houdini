"""This tool create a window to be able to import scene setup easily.
It's an alternative way to HDAs which are not the solution for all cases.

It lists all files and folders in the directory and show a combobox, files are prioritized over folders in
a reverse order. This allow the last setup (eg: setup_name_v12) to appear first.
If a folder is selected, it parse all files and folders in that folder and add a new combobox with the new entries.

You can hide the text area for the path directory to hide it from users and only let the TDs change it.
You can use the environment variable "HOUDINI_SETUPLOADER_PATH" instead of a path hardcoded in your script.

This tool can be used in any software just by inheriting SetupLoader() and implementing the import_file() function.
"""


import os
import functools
import logging
from PySide2 import QtCore, QtGui, QtWidgets
import lib.pythonlib.common
logger = logging.getLogger(__name__)


def get_entries(path):
    """Return all files and folders in the specified path, separated by type in a dictionary"""
    elements = os.listdir(path)
    files = [i for i in elements if os.path.isfile(os.path.join(path, i))]
    folders = [i for i in elements if os.path.isdir(os.path.join(path, i))]
    files = list(reversed(sorted(files, key=lib.pythonlib.common.natural_sort_key)))
    folders = list(reversed(sorted(folders, key=lib.pythonlib.common.natural_sort_key)))
    return {'folders': folders, 'files': files}


class SetupLoader(QtWidgets.QWidget):
    def __init__(self, path, hide_path=True, parent=None):
        super(SetupLoader, self).__init__(parent)
        self.menus = []
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.path = QtWidgets.QLineEdit()
        self.path.editingFinished.connect(self.change_path)
        self.path.textEdited.connect(self.change_path)
        self.path.textChanged.connect(self.change_path)
        self.combosLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout.addWidget(self.path)
        self.verticalLayout.addLayout(self.combosLayout)
        self.button = QtWidgets.QPushButton('Import')
        self.button.clicked.connect(self.import_file)
        self.verticalLayout.addWidget(self.button)
        self.path.setText(path)
        if hide_path:
            self.path.setVisible(False)

    def add_menu(self, data):
        """When the path or a combobox change, add a new combobox with the elements in data."""
        logger.debug('add_menu', data)
        combo = QtWidgets.QComboBox()
        self.menus += [combo]
        comboModel = combo.model()
        index = 0
        for typ in ['folders', 'files']:
            for name in data[typ]:
                item = QtGui.QStandardItem(name)
                comboModel.appendRow(item)
                combo.setItemData(index, {'type': typ, 'name': name})
                if typ == 'folders':
                    combo.model().item(index).setForeground(QtGui.QColor("#FFC733"))
                index += 1

        self.combosLayout.addWidget(combo)
        text = data['files'][0] if data['files'] else data['folders'][0] if data['folders'] else ''
        combo.currentIndexChanged.connect(functools.partial(self.changed_entry, combo))
        combo.activated.connect(functools.partial(self.changed_entry, combo))
        if text:
            index = combo.findText(text, QtCore.Qt.MatchFixedString)
            if index == combo.currentIndex():
                self.changed_entry(combo, index)  # If there are only folders force the refresh of sucessive directories
            else:
                combo.setCurrentIndex(index)
        self.set_button_state()
        return combo

    def set_button_state(self):
        """Set the import button state depending if the last combobox is a folder or a file."""
        combo = self.menus[-1]
        text = combo.currentText()
        index = combo.findText(text, QtCore.Qt.MatchFixedString)
        typ = combo.itemData(index)['type']
        if typ == 'files':
            self.button.setEnabled(True)
        else:
            self.button.setEnabled(False)

    def remove_menu(self):
        """Remove the last combobox on the right."""
        try:
            self.combosLayout.removeWidget(self.menus[-1])
            self.menus[-1].deleteLater()
            del self.menus[-1]
        except IndexError:
            pass

    def change_path(self):
        """Called when a new path is set in the LineEdit"""
        for i in self.menus:
            self.remove_menu()
        data = get_entries(self.path.text())
        logger.debug('Change Path:', self.path.text())
        self.add_menu(data)

    def changed_entry(self, combo, index):
        """Remove all comboboxes on the right of the combobox that changed.
        If the entry of the combobox is a file do nothing.
        If the entry of the combobox is a folder, list the data in the folder and create a combobox.
        """
        combo_nb = self.menus.index(combo) + 1
        for i in range(len(self.menus) - combo_nb):
            self.remove_menu()
        typ = combo.itemData(index)['type']
        if typ == 'folders':
            combo.setStyleSheet("QComboBox:editable { color: #FFC733}")
            path = self.current_path()
            data = get_entries(path)
            combo = self.add_menu(data)
        else:
            combo.setStyleSheet("QComboBox:editable { color: #FFF}")
        self.set_button_state()

    def current_path(self):
        """Rebuild the path from all combobox values."""
        path = []
        for count, _ in enumerate(self.menus):
            prev_index = self.menus[count].currentIndex()
            path += [self.menus[count].itemData(prev_index)['name']]
        path = os.path.join(self.path.text(), *path)
        return path

    def import_file(self):
        pass


class HoudiniSetupLoader(SetupLoader):
    def __init__(self, path, hide_path=True, parent=None):
        super(HoudiniSetupLoader, self).__init__(path, hide_path, parent)
        import hou
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)

    def import_file(self):
        import hou
        path = self.current_path()
        hou.hipFile.merge(path)


def open_houdini_setuploader(path, hide_path=True):
    if not path:
        path = os.environ.get('HOUDINI_SETUPLOADER_PATH')
    ui = HoudiniSetupLoader(path, hide_path)
    ui.show()
    return ui
