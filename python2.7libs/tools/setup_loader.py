# list all files and folders and sort files in reverse natural order with folders first in alphabetical order
# create a menu with all those entries and select the first file if any, otherwise the first folder
# if its a folder add a new menu and recall that function with the new path, deactivate the import button
# if its a file remove the name of the folder from the menu entry, activate the import button


# Create a window to import scene files in a folder. A bit like HDA but with scene files



import re
import os
import functools
from PySide2 import QtCore, QtGui, QtWidgets
import hou
import common.utils


MAINPATH = r'E:\Houdini\smoke'


def get_entries(path):
    elements = os.listdir(path)
    files = [i for i in elements if os.path.isfile(os.path.join(path, i))]
    folders = [i for i in elements if os.path.isdir(os.path.join(path, i))]
    files = list(reversed(sorted(files, key=common.utils.natural_sort_key)))
    folders = list(reversed(sorted(folders, key=common.utils.natural_sort_key)))
    return {'folders': folders, 'files': files}


class SetupLoader(QtWidgets.QWidget):
    def __init__(self, path, parent=None):
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
        self.button.clicked.connect(self.import2)
        self.verticalLayout.addWidget(self.button)

        self.path.setText(path)
        self.show()


    def add_menu(self, data):
        combo = QtWidgets.QComboBox()
        self.menus += [combo]
        comboModel = combo.model()
        index = 0
        for typ in ['folders', 'files']:
            for name in data[typ]:
                item = QtGui.QStandardItem(name)
                comboModel.appendRow(item)
                combo.setItemData(index, {'type': typ, 'name': name})
                index += 1

        self.combosLayout.addWidget(combo)
        text = data['files'][0] if data['files'] else data['folders'][0] if data['folders'] else ''
        combo.currentIndexChanged.connect(functools.partial(self.changed_entry, combo))
        combo.activated.connect(functools.partial(self.changed_entry, combo))
        if text:
            index = combo.findText(text, QtCore.Qt.MatchFixedString)
            combo.setCurrentIndex(index)
        self.set_button_state()
        return combo

    def set_button_state(self):
        combo = self.menus[-1]
        text = combo.currentText()
        index = combo.findText(text, QtCore.Qt.MatchFixedString)
        typ = combo.itemData(index)['type']
        if typ == 'files':
            self.button.setEnabled(True)
            print('enabled')
        else:
            print('disabled')
            self.button.setEnabled(False)



    def remove_menu(self):
        try:
            self.combosLayout.removeWidget(self.menus[-1])
            self.menus[-1].deleteLater()
            del self.menus[-1]
        except IndexError:
            pass


    def change_path(self):
        for i in self.menus:
            self.remove_menu()
        data = get_entries(self.path.text())
        self.add_menu(data)


    def changed_entry(self, combo, index):
        # remove all menus after the index of the current combo
        # if it's a folder list the content and create a menu accordingly
        # if it's a file do nothing
        combo_nb = self.menus.index(combo) + 1
        for i in range(len(self.menus) - combo_nb):
            pass
            self.remove_menu()
        typ = combo.itemData(index)['type']
        if typ == 'folders':
            path = []
            for count, _ in enumerate(self.menus):
                prev_index = self.menus[count].currentIndex()
                path += [self.menus[count].itemData(prev_index)['name']]
            path = os.path.join(self.path.text(), *path)
            data = get_entries(path)
            combo = self.add_menu(data)
        self.set_button_state()


    def current_path(self):
        path = []
        for count, _ in enumerate(self.menus):
            prev_index = self.menus[count].currentIndex()
            path += [self.menus[count].itemData(prev_index)['name']]
        path = os.path.join(self.path.text(), *path)
        return path


    def import2(self):
        path = self.current_path()
        hou.hipFile.merge(path)


dialog = SetupLoader()
