try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QAction
import hou
from lib.pythonlib.qt import *

class RowLayout(RowLayout):
    pass
    def addTextField(self):
        self.textfield = LineEditValueLadder(self.parent)
        self.textfields.append(self.textfield)
        self.addWidget(self.textfield)
        return self.textfield


class ValueLadderMixin():
    def __init__(self, *args, **kwargs):
        super(ValueLadderMixin, self).__init__(*args, **kwargs)
        self._pressed = False

    def mousePressEvent(self, event):
        # Show the value ladder window if MMB was pressed.
        if event.button() == Qt.MiddleButton:
            try:
                hou.ui.openValueLadder(float(self.text()), self._ladderchange, data_type=hou.valueLadderDataType.Float)
            except hou.OperationFailed:
                return  # A ladder is already open somewhere
            except ValueError:
                pass  # The value is not a float
            else:
                self._pressed = True
        super(ValueLadderMixin, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pressed:
            hou.ui.updateValueLadder(event.globalX(), event.globalY(), bool(event.modifiers() & Qt.AltModifier), bool(event.modifiers() & Qt.ShiftModifier))
        super(ValueLadderMixin, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._pressed:
            hou.ui.closeValueLadder()
            self._pressed = False

    def _ladderchange(self, new_value):
        self.setText(str(new_value))


class LineEditValueLadder(ValueLadderMixin, QtWidgets.QLineEdit):
    def mousePressEvent(self, event):
        super(LineEditValueLadder, self).mousePressEvent(event)
