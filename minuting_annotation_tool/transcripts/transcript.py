from PySide2.QtWidgets import QTableView
from PySide2.QtCore import Signal

class Transcript(QTableView):
    visible_rows_changed = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        _visible_rows = -1, -1
        self.setWordWrap(True)

    @property
    def visible_rows(self):
        return self._visible_rows

    @visible_rows.setter
    def visible_rows(self, value):
        self._visible_rows = value
        for r in range(*value):
            self.resizeRowToContents(r)
        self.visible_rows_changed.emit(value)

    def get_visible_rows(self):
        s = self.rowAt(0)
        e = self.rowAt(self.height())
        if e < 0:
            e = self.model().rowCount()
        return s, e

    def dataChanged(self, QModelIndex, QModelIndex_, roles=[]):
        self.visible_rows = self.get_visible_rows()
        return super().dataChanged(self, QModelIndex, QModelIndex_, roles=roles)

    def resizeEvent(self, event):
        self.visible_rows = self.get_visible_rows()
        return super().resizeEvent(event)
    
    def verticalScrollbarValueChanged(self, i):
        self.visible_rows = self.get_visible_rows()
        return super().verticalScrollbarValueChanged(i)