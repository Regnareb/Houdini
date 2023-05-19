import logging
from PySide2 import QtCore, QtGui, QtWidgets
import hou
logger = logging.getLogger(__name__)


def set_preference(name, value):
    if not hou.getPreference(name):
        hou.addPreference(name, value)
    else:
        hou.setPreference(name, value)


class Preferences(QtWidgets.QDialog):
    def __init__(self):
        super(Preferences, self).__init__(hou.ui.mainQtWindow())
        # self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        self.setWindowTitle('Beranger Preferences')

        self.transfer_display_node = QtWidgets.QCheckBox('Transfer Display Flag on connection')
        self.create_null_shift_click = QtWidgets.QCheckBox('Create a NULL when shift clicking with a node selected')
        self.scrub_timeline_mode = QtWidgets.QComboBox('Scrub Timeline tool relative mode')
        self.scrub_timeline_keep_pressed = QtWidgets.QCheckBox('Scrub Timeline tool shortcut need to be kept pressed')
        self.drag_and_drop_in_context = QtWidgets.QCheckBox('Always try to create drag and dropped files in the current context')

        self.row_layout = QtWidgets.QVBoxLayout()
        self.row_layout.addWidget(self.transfer_display_node)
        self.row_layout.addWidget(self.create_null_shift_click)
        self.row_layout.addWidget(self.scrub_timeline_mode)
        self.row_layout.addWidget(self.scrub_timeline_keep_pressed)
        self.row_layout.addWidget(self.drag_and_drop_in_context)
        self.row_layout.addStretch()

        self.apply = QtWidgets.QPushButton('Apply')
        self.accept = QtWidgets.QPushButton('Accept')
        self.close = QtWidgets.QPushButton('Close')
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.apply)
        self.buttons_layout.addWidget(self.close)

        self.row_layout.addLayout(self.buttons_layout)
        self.setLayout(self.row_layout)
        # self.setContentsMargins(0,0,0,0)


def show():
    ui = Preferences()
    ui.show()
    return ui
