import os
import io
from itertools import takewhile

from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QTableView, QCheckBox, QMenu, QAbstractItemView, QSizePolicy, QAction, QPlainTextEdit
from PySide2.QtCore import QItemSelectionModel, Slot
from PySide2.QtGui import QKeySequence, QTextBlockFormat, QTextCursor
from PySide2 import QtWidgets
from PySide2.QtCore import Qt, QPoint, QModelIndex, Signal
from PySide2 import QtGui

from minutes.minutes_model import MinutesModel
from annotation import Annotation, Minute
from transcripts.transcript import Transcript

class Minutes(QWidget):
    def __init__(self, annotation : Annotation, *args, **kwargs):
        super(Minutes, self).__init__(*args, **kwargs)
        self.annotation = annotation
        self.annotation.path_changed.connect(self.set_path)
        self.annotation.modified_changed.connect(self._modified)
        self._gui_setup()

    def set_path(self):
        self.minutes_ver.clear()
        self.minutes_ver.addItems(self.annotation.minutes_files)
        
    def _gui_setup(self):
        layout = QVBoxLayout(self)

        # current transcript
        label = QLabel(self)
        label.setText('Minutes:')
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        minutes_ver = QComboBox(self)
        minutes_ver.setEditable(False)
        minutes_ver.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        minutes_ver.currentTextChanged.connect(self._minutes_changed)
        self.minutes_ver = minutes_ver

        edit = QCheckBox(self)
        edit.setText("edit minutes")
        edit.setChecked(True)
        self.edit = edit

        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(label)
        minutes_layout.addWidget(minutes_ver)
        minutes_layout.addWidget(edit)
        layout.addLayout(minutes_layout)

        minutes_view = TableView(self)
        minutes_view.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.minutes_view = minutes_view
        self.model = MinutesModel(self.annotation)
        minutes_view.setModel(self.model)
        header = minutes_view.horizontalHeader()
        header.stretchLastSection()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        edit.stateChanged.connect(self._editation)
        layout.addWidget(minutes_view)

        insert = QAction('Insert', minutes_view)
        insert.setShortcuts(['Shift+I', 'Shift+Insert'])
        insert.triggered.connect(self._insert_triggered)
        self.insert = insert
        minutes_view.addAction(insert)

        delete = QAction('Delete', minutes_view)
        delete.setShortcuts(['Shift+D', 'Shift+Del'])
        delete.triggered.connect(self._delete_triggered)
        self.delete = delete
        minutes_view.addAction(delete)
        minutes_view.minute_selected.connect(self._minute_selected)
        self.setLayout(layout)
        edit.setChecked(False)

    @Slot()
    def _insert_triggered(self):
        r = self.selected_rows()
        nr = Minute()
        if len(r) > 0:
            r = r[-1] + 1
        else:
            r = self.annotation.minutes_count()
        self.model.insertRow(r, nr)

        self.minutes_view.selectRow(r)
        #self.minutes_view.setCurrentIndex(self.model.index(r, 1))

    @Slot()
    def _delete_triggered(self):
        r = self.selected_rows()
        self.model.removeRows(r[0], len(r))

    def _editation(self, s):
        self.insert.setEnabled(s)
        self.delete.setEnabled(s)
        if s:
            self.minutes_view.setEditTriggers(QAbstractItemView.AllEditTriggers)
        else:
            self.minutes_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def _minute_selected(self, m):
        if self.edit.isChecked():
            self.delete.setEnabled(True)
            return
        m = self.annotation.get_minute(m)
        self.annotation.set_minute(m)

    @Slot(bool)
    def _modified(self, m=True):
        self.minutes_ver.setEnabled(not m)
        if m:
            self.minutes_ver.setToolTip('Minutes were modified. Save the changes first!')

    @Slot()
    def _selection_changed(self):
        selected_rows = self.selected_rows()
        if len(selected_rows) == 0:
            self.delete.setEnabled(False)
        else:
            self.delete.setEnabled(True)

    def selected_rows(self):
        selection = self.minutes_view.selectionModel()
        return list(set([i.row() for i in selection.selectedIndexes()]))
        
    @Slot()
    def _minutes_changed(self):
        self.annotation.open_minutes(self.minutes_ver.currentText())

class TableView(Transcript):
    minute_selected = Signal(int)

    def __init__(self, parent):
        super(TableView, self).__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mouseDoubleClickEvent(self, event):
        idx = self.selectedIndexes()
        if len(idx) > 0:
            idx = idx[0].row()
            self.minute_selected.emit(idx)
            self.clearSelection()
        return super().mouseDoubleClickEvent(event)