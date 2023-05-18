from copy import copy
import os

from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QCheckBox, QAbstractItemView, QSizePolicy, QAction, QUndoCommand, QToolBar
from PySide2.QtCore import QSettings, Slot, Qt, Signal
from PySide2 import QtWidgets
from PySide2.QtGui import QIcon, QKeyEvent

from .minutes_model import MinutesModel
from ..annotation import Annotation, Minute
from ..transcripts.transcript import Transcript
from .minutes_editor import MinutesEditor
from ..transcripts.dialog_act_editor import DialogActEditor
from ..combobox import ComboBox

class Minutes(QWidget):
    def __init__(self, annotation : Annotation, *args, **kwargs):
        super(Minutes, self).__init__(*args, **kwargs)
        self._evaluation_mode = False
        self.annotation = annotation
        self.annotation.path_changed.connect(self.set_path)
        self.annotation.modified_changed.connect(self._modified)
        self.indent = QSettings().value('indent')
        self._gui_setup()

    def set_evaluation_mode(self, evaluation):
        self._evaluation_mode = evaluation
        self.model.set_evaluation_mode(evaluation)

        self.edit.setChecked(False)
        self.edit.setEnabled(not evaluation)
        self._editation(False)

    def set_path(self):
        self.minutes_ver.clear()
        self.minutes_ver.addItems(self.annotation.minutes_files)
        
    def _gui_setup(self):
        layout = QVBoxLayout(self)

        # current minutes
        label = QLabel(self)
        label.setText('Minutes:')
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        minutes_ver = ComboBox(self)
        self.minutes_ver = minutes_ver
        minutes_ver.setEditable(False)
        minutes_ver.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        minutes_ver.currentTextChanged.connect(self._minutes_changed)
        minutes_ver.focused.connect(self.update_minutes)

        self.edit = QCheckBox(self)
        self.edit.setText("edit minutes")
        self.edit.setChecked(True)

        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(label)
        minutes_layout.addWidget(minutes_ver)
        layout.addLayout(minutes_layout)

        minutes_view = TableView(self)
        minutes_view.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.editor = DialogActEditor(self)
        minutes_view.setItemDelegateForColumn(0, self.editor)
        self.minutes_view = minutes_view
        self.model = MinutesModel(self.annotation)
        minutes_view.setModel(self.model)
        header = minutes_view.horizontalHeader()
        header.stretchLastSection()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        
        self.edit.stateChanged.connect(self._editation)

        #create toolbar and add all actions to it

        self.toolbar = QToolBar("Minutes toolbar")
        self.toolbar.setMovable(False)
        layout.addWidget(self.toolbar)

        self.insertingAction = QAction('Insert line below', minutes_view)
        self.insertingAction.setShortcuts(['alt+I', '+Insert'])
        self.insertingAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"../icons/layout-split-vertical.png")))
        self.insertingAction.setToolTip('Insert row (Alt+I)')
        self.insertingAction.triggered.connect(self._insert_triggered)
        self.toolbar.addAction(self.insertingAction)

        self.deleteAction = QAction('Delete', minutes_view)
        self.deleteAction.setShortcuts(['alt+D', 'alt+Del'])
        self.deleteAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"../icons/layout-join-vertical.png")))
        self.deleteAction.setToolTip("Delete row (Alt+D)")
        self.deleteAction.triggered.connect(self._delete_triggered)
        self.toolbar.addAction(self.deleteAction)

        self.joinDownAction = QAction('Join down', minutes_view)
        self.joinDownAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"../icons/arrow-stop-270.png")))
        self.joinDownAction.triggered.connect(self._join_down_triggerd)
        self.toolbar.addAction(self.joinDownAction)

        self.joinUpAction = QAction('Join up', minutes_view)
        self.joinUpAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"../icons/arrow-stop-090.png")))
        self.joinUpAction.triggered.connect(self._join_up_triggerd)
        self.toolbar.addAction(self.joinUpAction)

        self.splitAction = QAction('Split at cursor (Ctrl+Enter)', minutes_view)
        self.splitAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"../icons/arrow-split-270.png")))
        self.splitAction.triggered.connect(self._split_triggered)
        self.toolbar.addAction(self.splitAction)

        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(empty)

        self.toolbar.addWidget(self.edit)

        layout.addWidget(minutes_view)

        right = QAction('Indent right', minutes_view)
        right.setShortcuts(['alt+R', 'alt+Del'])
        right.triggered.connect(self._right_triggered)
        self.right = right
        minutes_view.addAction(right)

        left = QAction('Indent left', minutes_view)
        left.setShortcuts(['alt+L', 'alt+Del'])
        left.triggered.connect(self._left_triggered)
        self.left = left
        minutes_view.addAction(left)

        minutes_view.minute_selected.connect(self._minute_selected)
        self.setLayout(layout)
        self.edit.setChecked(False)

    @Slot()
    def update_minutes(self):
        old = set(self.annotation.minutes_files)
        self.annotation.refresh()
        new = set(self.annotation.minutes_files)
        if len(old-new) > 0 or len(new-old) > 0:
            self.minutes_ver.clear()
            self.minutes_ver.addItems(new)


    @Slot()
    def _right_triggered(self):
        r = self.selected_rows()
        for idx in r:
            m = self.annotation.get_minute(idx)
            m.text = f'{self.indent}{m.text}'
        self.annotation.modified = True
        self.model.update()

    @Slot()
    def _left_triggered(self):
        r = self.selected_rows()
        for idx in r:
            m = self.annotation.get_minute(idx)
            m.text = m.text.replace(self.indent, '', 1)
        self.annotation.modified = True
        self.model.update()

    @Slot()
    def _insert_triggered(self):
        if self._evaluation_mode:
            return
        r = self.selected_rows()
        if len(r) == 0:
            return
        r = r[-1] + 1
        nr = Minute()

        command = InsertCommand(self, r, nr, "Insert minutes line")
        self.annotation.push_to_undo_stack(command)

        self.minutes_view.selectRow(r)
        #self.minutes_view.setCurrentIndex(self.model.index(r, 1))

    @Slot()
    def _delete_triggered(self):
        if self._evaluation_mode:
            return
        r = self.selected_rows()

        command = DeleteCommand(self, r[0], "Delete minutes line")
        self.annotation.push_to_undo_stack(command)

    @Slot()
    def _join_up_triggerd(self):
        sel = self.minutes_view.selectionModel().selectedRows()
        if len(sel) == 0:
            return
        r = sel[-1].row()
        if r <= 0:
            return
        if self.editor.editor:
            self.editor.editor.clearFocus()
        command = JoinUpCommand(self, r, r-1, f"Join minutes line {r} to {r-1}")
        self.annotation.push_to_undo_stack(command)

    @Slot()
    def _join_down_triggerd(self):
        sel = self.minutes_view.selectionModel().selectedRows()
        if len(sel) == 0:
            return
        r = sel[0].row()
        if r >= self.annotation.das_count()-1:
            return
        if self.editor.editor:
            self.editor.editor.clearFocus()
        command = JoinDownCommand(self, r, r+1, f"Join minutes line {r} to {r+1}")
        self.annotation.push_to_undo_stack(command)

    @Slot()
    def _split_triggered(self):
        if self.editor.editor:
            QApplication.postEvent(self.editor.editor, QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Enter, Qt.ControlModifier))

    def _editation(self, s):
        self.insertingAction.setEnabled(s and not self._evaluation_mode)
        self.deleteAction.setEnabled(s and not self._evaluation_mode)
        self.joinDownAction.setEnabled(s and not self._evaluation_mode)
        self.joinUpAction.setEnabled(s and not self._evaluation_mode)
        self.splitAction.setEnabled(s and not self._evaluation_mode)
        self.left.setEnabled(s and not self._evaluation_mode)
        self.right.setEnabled(s and not self._evaluation_mode)
        if s or self._evaluation_mode:
            self.minutes_view.setEditTriggers(QAbstractItemView.AllEditTriggers)
        else:
            self.minutes_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def _minute_selected(self, m):
    #     if self._evaluation_mode:
    #         return
        if self.edit.isChecked():
            self.deleteAction.setEnabled(True)
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
            self.deleteAction.setEnabled(False)
        else:
            self.deleteAction.setEnabled(True)

    def selected_rows(self):
        selection = self.minutes_view.selectionModel()
        return list(set([i.row() for i in selection.selectedIndexes()]))
        
    @Slot()
    def _minutes_changed(self):
        self.annotation.undo_stack.clear()
        self.annotation.open_minutes(self.minutes_ver.currentText())
        self.annotation.copy_problems_if_none_presend()
        self.annotation.problems_changed.emit()

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

class InsertCommand(QUndoCommand):
    def __init__(self, minutes, row_index, new_minute, text : str):
        super().__init__(text)
        self.minutes = minutes
        self.row_index = row_index
        self.new_minute = new_minute

    def redo(self):
        self.minutes.model.insertRow(self.row_index, self.new_minute)

    def undo(self):
        self.minutes.model.removeRows(self.row_index, 1)

class DeleteCommand(QUndoCommand):
    def __init__(self, minutes, row_index, text : str):
        super().__init__(text)
        self.minutes = minutes
        self.row_index = row_index

    def redo(self):
        self.old_line = self.minutes.annotation.get_minute(self.row_index)
        self.minutes.model.removeRows(self.row_index, 1)

    def undo(self):
        self.minutes.model.insertRow(self.row_index, self.old_line)


class JoinUpCommand(QUndoCommand):
    def __init__(self, minutes, what, to, text):
        super().__init__(text)
        self.minutes = minutes
        self.what = what
        self.to = to

    def redo(self):
        self.first_old_line = copy(self.minutes.annotation.get_minute(self.to))
        self.second_old_line = copy(self.minutes.annotation.get_minute(self.what))
        self.minutes.annotation.get_minute(self.to).text = f"{self.first_old_line.text} {self.second_old_line.text}"
        self.minutes.annotation.remove_minutes(self.what, 1)

    def undo(self):
        self.minutes.annotation.remove_minutes(self.to, 1)
        self.minutes.annotation.insert_minute(self.to, self.first_old_line)
        self.minutes.annotation.insert_minute(self.what, self.second_old_line)

class JoinDownCommand(QUndoCommand):
    def __init__(self, minutes, what, to, text):
        super().__init__(text)
        self.minutes = minutes
        self.what = what
        self.to = to

    def redo(self):
        self.first_old_line = copy(self.minutes.annotation.get_minute(self.what))
        self.second_old_line = copy(self.minutes.annotation.get_minute(self.to))
        self.minutes.annotation.get_minute(self.to).text = f"{self.first_old_line.text} {self.second_old_line.text}"
        self.minutes.annotation.remove_minutes(self.what, 1)

    def undo(self):
        self.minutes.annotation.remove_minutes(self.what, 1)
        self.minutes.annotation.insert_minute(self.what, self.first_old_line)
        self.minutes.annotation.insert_minute(self.to, self.second_old_line)