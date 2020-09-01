import PySide2
from PySide2.QtWidgets import QComboBox
from PySide2.QtCore import Signal

class ComboBox(QComboBox):
    focused = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    def focusInEvent(self, event: PySide2.QtGui.QFocusEvent):
        self.focused.emit()
        return super().focusInEvent(event)
