import re
from copy import copy

from PySide2.QtWidgets import QApplication, QLineEdit, QPushButton, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QCheckBox, QAbstractItemView, QSizePolicy, QAction, QUndoCommand, QToolBar
from PySide2.QtCore import Qt, Slot, Signal
from PySide2.QtGui import QIcon, QKeyEvent
from PySide2 import QtWidgets
from ..transcripts.dialog_act_model import DAModel
from ..transcripts.speaker_editor import SpeakerEditor
from ..transcripts.dialog_act_editor import DialogActEditor
from ..transcripts.transcript import Transcript
from ..annotation import Annotation, DialogAct
from ..combobox import ComboBox

class Transcripts(QWidget):
    edit_mode_changed = Signal(bool)

    def __init__(self, annotation : Annotation, *args, **kwargs):
        super(Transcripts, self).__init__(*args, **kwargs)
        self._evaluation_mode = False
        self.annotation = annotation
        self.annotation.path_changed.connect(self.set_path)
        self._gui_setup()
        
    def _gui_setup(self):
        layout = QVBoxLayout(self)

        # current transcript
        label = QLabel(self)
        label.setText('Transcript:')
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        transcript_ver = ComboBox(self)
        transcript_ver.setEditable(False)
        transcript_ver.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        transcript_ver.currentTextChanged.connect(self._transcript_changed)
        transcript_ver.focused.connect(self.update_transcripts)
        self.transcript_ver = transcript_ver

        transcript_layout = QHBoxLayout()
        transcript_layout.addWidget(label)
        transcript_layout.addWidget(transcript_ver)
        layout.addLayout(transcript_layout)

        transcript = Transcript(self)
        transcript.setEditTriggers(QAbstractItemView.NoEditTriggers)
        transcript.visible_rows_changed.connect(self._visible_rows_changed)
        transcript.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.transcript = transcript

        #create toolbar and add all actions to it

        self.toolbar = QToolBar("Transcript toolbar")
        self.toolbar.setMovable(False)
        layout.addWidget(self.toolbar)

        self.insertingAction = QAction('Insert row', transcript)
        self.insertingAction.setShortcuts(['Ctrl+I', 'Insert'])
        self.insertingAction.setIcon(QIcon("alignmeet/icons/layout-split-vertical.png"))
        self.insertingAction.setToolTip('Insert row (Ctrl+I)')
        self.insertingAction.triggered.connect(self._insert_triggered)
        self.toolbar.addAction(self.insertingAction)
        
        self.deleteAction = QAction('Delete selected', transcript)
        self.deleteAction.setShortcuts(['Ctrl+D', 'Del'])
        self.deleteAction.setIcon(QIcon("alignmeet/icons/layout-join-vertical.png"))
        self.deleteAction.setToolTip("Delete selected (Ctrl+D)")
        self.deleteAction.triggered.connect(self._delete_triggered)
        self.toolbar.addAction(self.deleteAction)

        self.joinDownAction = QAction('Join down', transcript)
        self.joinDownAction.setIcon(QIcon("alignmeet/icons/arrow-stop-270.png"))
        self.joinDownAction.triggered.connect(self._join_down_triggerd)
        self.toolbar.addAction(self.joinDownAction)

        self.joinUpAction = QAction('Join up', transcript)
        self.joinUpAction.setIcon(QIcon("alignmeet/icons/arrow-stop-090.png"))
        self.joinUpAction.triggered.connect(self._join_up_triggerd)
        self.toolbar.addAction(self.joinUpAction)

        self.splitAction = QAction('Split at cursor (Ctrl+Enter)', transcript)
        self.splitAction.setIcon(QIcon("alignmeet/icons/arrow-split-270.png"))
        self.splitAction.triggered.connect(self._split_triggered)
        self.toolbar.addAction(self.splitAction)

        self.toolbar.addSeparator()

        self.resetAction = QAction('Reset minutes', transcript)
        self.resetAction.setShortcuts(['Ctrl+m'])
        self.resetAction.setToolTip('Reset minutes (Ctrl+m)')
        self.resetAction.triggered.connect(self._reset_triggered)
        transcript.addAction(self.resetAction)
        self.toolbar.addAction(self.resetAction)
        
        self.resetpAction = QAction('Reset problems', transcript)
        self.resetpAction.setShortcuts(['Ctrl+p'])
        self.resetpAction.setToolTip('Reset problems (Ctrl+p)')
        self.resetpAction.triggered.connect(self._resetp_triggered)
        transcript.addAction(self.resetpAction)
        self.toolbar.addAction(self.resetpAction)

        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(empty)

        self.edit = QCheckBox("edit transcript")
        self.edit.setChecked(True)
        self.edit.stateChanged.connect(self._editation)
        # parse_layout.addStretch()

        self.problems = QCheckBox('show problems')
        self.problems.setChecked(True)

        self.toolbar.addWidget(self.edit)
        self.toolbar.addWidget(self.problems)


        layout.addWidget(transcript)
        model = DAModel(self.annotation, transcript)
        self.annotation.modified_changed.connect(lambda : self._visible_rows_changed(self.transcript.get_visible_rows()))
        self.annotation.modified_changed.connect(self._modified)
        self.model = model
        transcript.setModel(model)
        transcript.setSelectionBehavior(QAbstractItemView.SelectRows)
        selection_model = transcript.selectionModel()
        selection_model.selectionChanged.connect(self._selection_changed)
        self.editor = DialogActEditor(self)
        self.editor.end_editing.connect(self._editor_closed)
        self.editor.remove_row.connect(self._delete_triggered)
        transcript.setItemDelegateForColumn(1, self.editor)
        self.speaker_editor = SpeakerEditor(self)
        transcript.setItemDelegateForColumn(0, self.speaker_editor)
        self.problems.stateChanged.connect(lambda x: transcript.showColumn(2) if self.problems.isChecked() else transcript.hideColumn(2))
        header = transcript.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)


        a = QAction('', self)
        a.setSeparator(True)
        transcript.addAction(a)

        expand = QAction('Expand speakers', transcript)
        expand.setShortcuts(['Ctrl+E'])
        expand.triggered.connect(self._expand_triggered)
        self.expand = expand
        transcript.addAction(expand)

        self.setLayout(layout)
        self.edit.setChecked(False)

        search_layout = QHBoxLayout()
        layout.addLayout(search_layout)

        self.matches = []
        self.current = None
        search = QLineEdit(self)
        search.returnPressed.connect(lambda: self.next(True))
        search.textChanged.connect(self.seach_changed)
        search.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        search_layout.addWidget(search)
        self.search = search

        previous = QPushButton('Previous', self)
        previous.setShortcut('Ctrl+G')
        previous.clicked.connect(lambda: self.next(False))
        search_layout.addWidget(previous)

        next = QPushButton('Next', self)
        next.setShortcut('Ctrl+F')
        next.clicked.connect(lambda: self.next(True))
        search_layout.addWidget(next)

        search_options_layout = QHBoxLayout()
        layout.addLayout(search_options_layout)

        search_status = QLabel('0 matches', self)
        self.search_status = search_status
        search_options_layout.addWidget(search_status)

        search_options_layout.addStretch()

        self.only_matches = QCheckBox('show matches only')
        self.only_matches.setChecked(False)
        self.only_matches.stateChanged.connect(lambda: self.seach_changed(search.text()))
        search_options_layout.addWidget(self.only_matches)

        self.ignore_case = QCheckBox('ignore case')
        self.ignore_case.setChecked(True)
        self.ignore_case.stateChanged.connect(lambda: self.seach_changed(search.text()))
        search_options_layout.addWidget(self.ignore_case)
        
    def next(self, next):
        if len(self.matches) > 0:
            d = 1 if next else -1
            if self.current is None:
                self.current = -1 if next else len(self.matches)
            self.current = (self.current + d) % len(self.matches)
            index = self.model.index(self.matches[self.current], 0)
            self.transcript.clearSelection()
            self.transcript.scrollTo(index)
            self.transcript.selectRow(self.matches[self.current])
            self.search_status.setText(f'Match {self.current + 1}/{len(self.matches)}')
        else:
            if not self.search.hasFocus():
                self.search.setFocus(Qt.ShortcutFocusReason)
            self.search_status.setText('0 matches')

    def seach_changed(self, text):
        matches = []
        flags = re.UNICODE
        if self.ignore_case.isChecked():
            flags |= re.IGNORECASE
        valid = False
        try:
            ex = re.compile(text, flags)
            valid = True
        except:
            ex = re.compile('', flags)
        
        for i in range(self.annotation.das_count()):
            d = self.annotation.get_dialog_act(i)
            if ex.search(d.text) is not None or ex.search(d.speaker) is not None:
                matches.append(i)
                self.transcript.setRowHidden(i, False)
            else:
                self.transcript.setRowHidden(i, self.only_matches.isChecked())
        if valid:
            self.search_status.setText(f'{len(matches)} matches')
            self.search.setStyleSheet("")
            
            self.model.highlight = ex if len(text) > 0 else None
        else:
            self.model.highlight = None
            self.search_status.setText(f'Invalid regular expression')
            self.search.setStyleSheet("QLineEdit { background-color: red }")

        self.model.update()
        self.matches = matches
        self.current = None

    def set_evaluation_mode(self, evaluation):
        self._evaluation_mode = evaluation

        self.edit.setChecked(False)
        self.edit.setEnabled(not evaluation)
        self._editation(False)
    
    def set_path(self):
        self.transcript_ver.clear()
        self.transcript_ver.addItems(self.annotation.transcript_files)

    @Slot()
    def update_transcripts(self):
        old = set(self.annotation.transcript_files)
        self.annotation.refresh()
        new = set(self.annotation.transcript_files)
        if len(old-new) > 0 or len(new-old) > 0:
            self.transcript_ver.clear()
            self.transcript_ver.addItems(new)

    @Slot()
    def _expand_triggered(self):
        self.annotation.expand_speakers()

    def _editation(self, s):
        self.insertingAction.setEnabled(s)
        self.deleteAction.setEnabled(s)
        self.joinUpAction.setEnabled(s)
        self.joinDownAction.setEnabled(s)
        self.expand.setEnabled(s)
        if s:
            self.transcript.setEditTriggers(QAbstractItemView.AllEditTriggers)
        else:
            self.transcript.setEditTriggers(QAbstractItemView.NoEditTriggers)
        

    @Slot(tuple)
    def _visible_rows_changed(self, rows):
        m = set()
        s,e = rows
        if s >= 0:
            for i in range(s, e):
                mi = self.annotation.get_dialog_act(i).minute
                if mi is not None:
                    m.add(mi)
        self.annotation.visible_minutes = m

    def selected_rows(self):
        selection = self.transcript.selectionModel().selectedIndexes()
        return set([self.annotation.get_dialog_act(i.row()) for i in selection])

    @Slot(bool)
    def _modified(self, m):
        self.transcript_ver.setEnabled(not m)
        if m:
            self.transcript_ver.setToolTip('Trancript was modified. Save the changes first!')

    @Slot()
    def _editor_closed(self):
        return
        selection = self.transcript.selectionModel()
        selected_rows = list(set([i.row() for i in selection.selectedIndexes()]))
        if len(selected_rows) > 0:
            pass
            #self.transcript.selectRow(selected_rows[-1] + 1)
            #self.transcript.setCurrentIndex(self.model.index(selected_rows[-1] + 1, 1))

    @Slot()
    def _selection_changed(self):
        selected_rows = self.selected_rows()
        self.annotation.selected_das = selected_rows
        if self.edit.isChecked():
            self.deleteAction.setEnabled(len(selected_rows) > 0 and not self._evaluation_mode)
        self.resetAction.setEnabled(len(selected_rows) > 0 and not self._evaluation_mode)
        self.resetpAction.setEnabled(len(selected_rows) > 0 and not self._evaluation_mode)

    @Slot()
    def _insert_triggered(self):
        r = self.transcript.selectionModel().selectedIndexes()
        nr = DialogAct()
        if len(r) > 0:
            r = r[-1].row() + 1
            nr = copy(self.annotation.get_dialog_act(r - 1))
            nr.text = ''
        else:
            r = self.annotation.das_count()
        command = InsertCommand(self, r, nr, "Insert transcript line")
        self.annotation.push_to_undo_stack(command)

    @Slot()
    def _reset_triggered(self):
        self.annotation.set_minute()

    @Slot()
    def _resetp_triggered(self):
        self.annotation.set_problem()

    @Slot()
    def _delete_triggered(self):
        r = list(set([x.row() for x in self.transcript.selectionModel().selectedRows()]))
        if len(r) == 0:
            return
        command = DeleteCommand(self, r, f"Delete transcript line {r}")
        self.annotation.push_to_undo_stack(command)
    
    @Slot()
    def _join_up_triggerd(self):
        r = self.transcript.selectionModel().selectedRows()[-1].row()
        if r <= 0:
            return
        if self.editor.editor:
            self.editor.editor.clearFocus()
        command = JoinUpCommand(self, r, r-1, f"Join line {r} to {r-1}")
        self.annotation.push_to_undo_stack(command)

    @Slot()
    def _join_down_triggerd(self):
        r = self.transcript.selectionModel().selectedRows()[0].row()
        if r >= self.annotation.das_count()-1:
            return
        if self.editor.editor:
            self.editor.editor.clearFocus()
        command = JoinDownCommand(self, r, r+1, f"Join line {r} to {r+1}")
        self.annotation.push_to_undo_stack(command)

    @Slot()
    def _split_triggered(self):
        QApplication.postEvent(self.editor.editor, QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Enter, Qt.ControlModifier))

        
    @Slot()
    def _transcript_changed(self):
        self.annotation.undo_stack.clear()
        t = self.transcript_ver.currentText()
        self.annotation.open_transcript(t)

class InsertCommand(QUndoCommand):
    def __init__(self, transcripts, row_index, new_da, text : str):
        super().__init__(text)
        self.transcripts = transcripts
        self.row_index = row_index
        self.new_da = new_da

    def redo(self):
        self.transcripts.model.insertRow(self.row_index, self.new_da)

    def undo(self):
        self.transcripts.model.removeRows(self.row_index, 1)

class DeleteCommand(QUndoCommand):
    def __init__(self, transcripts, row_indices, text : str):
        super().__init__(text)
        self.transcripts = transcripts
        self.row_indices = row_indices

    def redo(self):
        self.old_lines = [self.transcripts.annotation.get_dialog_act(row_index) for row_index in self.row_indices]
        self.transcripts.model.removeRows(self.row_indices[0], len(self.row_indices))

    def undo(self):
        for old_line, row_index in zip(self.old_lines, self.row_indices):
            self.transcripts.model.insertRow(row_index, old_line)

class JoinUpCommand(QUndoCommand):
    def __init__(self, transctipts, what, to, text):
        super().__init__(text)
        self.transctipts = transctipts
        self.what = what
        self.to = to

    def redo(self):
        self.first_old_line = copy(self.transctipts.annotation.get_dialog_act(self.to))
        self.second_old_line = copy(self.transctipts.annotation.get_dialog_act(self.what))
        self.transctipts.annotation.get_dialog_act(self.to).text = f"{self.first_old_line.text}{self.second_old_line.text}"
        self.transctipts.annotation.remove_das(self.what, 1)

    def undo(self):
        self.transctipts.annotation.remove_das(self.to, 1)
        self.transctipts.annotation.insert_da(self.to, self.first_old_line)
        self.transctipts.annotation.insert_da(self.what, self.second_old_line)

class JoinDownCommand(QUndoCommand):
    def __init__(self, transctipts, what, to, text):
        super().__init__(text)
        self.transctipts = transctipts
        self.what = what
        self.to = to

    def redo(self):
        self.first_old_line = copy(self.transctipts.annotation.get_dialog_act(self.what))
        self.second_old_line = copy(self.transctipts.annotation.get_dialog_act(self.to))
        self.transctipts.annotation.get_dialog_act(self.to).text = f"{self.first_old_line.text}{self.second_old_line.text}"
        self.transctipts.annotation.remove_das(self.what, 1)

    def undo(self):
        self.transctipts.annotation.remove_das(self.what, 1)
        self.transctipts.annotation.insert_da(self.what, self.first_old_line)
        self.transctipts.annotation.insert_da(self.to, self.second_old_line)
