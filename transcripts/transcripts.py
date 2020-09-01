import os
import io
from copy import copy

from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTableView, QCheckBox, QMenu, QAbstractItemView, QSizePolicy, QAction
from PySide2.QtCore import QItemSelectionModel, Slot
from PySide2.QtGui import QKeySequence
from PySide2 import QtWidgets
from PySide2.QtCore import Qt, QPoint, QModelIndex, Signal
from PySide2 import QtGui
from transcripts.dialog_act_model import DAModel
from transcripts.speaker_editor import SpeakerEditor
from transcripts.dialog_act_editor import DialogActEditor
from transcripts.transcript import Transcript
from annotation import Annotation, DialogAct
from combobox import ComboBox

class Transcripts(QWidget):
    def __init__(self, annotation : Annotation, *args, **kwargs):
        super(Transcripts, self).__init__(*args, **kwargs)
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

        parse_layout = QHBoxLayout()
        edit = QCheckBox(self)
        edit.setText("edit transcript")
        edit.setChecked(True)
        edit.stateChanged.connect(self._editation)
        parse_layout.addStretch()
        parse_layout.addWidget(edit)

        self.edit = edit
        self.problems = QCheckBox('show problems')
        self.problems.setChecked(True)
        parse_layout.addWidget(self.problems)
        layout.addLayout(parse_layout)

        transcript = Transcript(self)
        transcript.setEditTriggers(QAbstractItemView.NoEditTriggers)
        transcript.visible_rows_changed.connect(self._visible_rows_changed)
        transcript.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.transcript = transcript
        layout.addWidget(transcript)
        model = DAModel(self.annotation, transcript)
        self.annotation.modified_changed.connect(lambda : self._visible_rows_changed(self.transcript.get_visible_rows()))
        self.annotation.modified_changed.connect(self._modified)
        self.model = model
        transcript.setModel(model)
        transcript.setSelectionBehavior(QAbstractItemView.SelectRows)
        selection_model = transcript.selectionModel()
        selection_model.selectionChanged.connect(self._selection_changed)
        editor = DialogActEditor(self)
        editor.end_editing.connect(self._editor_closed)
        editor.remove_row.connect(self._delete_triggered)
        transcript.setItemDelegateForColumn(1, editor)
        self.speaker_editor = SpeakerEditor(self)
        transcript.setItemDelegateForColumn(0, self.speaker_editor)
        self.problems.stateChanged.connect(lambda x: transcript.showColumn(2) if self.problems.isChecked() else transcript.hideColumn(2))
        header = transcript.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        insert = QAction('Insert', transcript)
        insert.setShortcuts(['Ctrl+I', 'Insert'])
        insert.triggered.connect(self._insert_triggered)
        self.insert = insert
        transcript.addAction(insert)

        delete = QAction('Delete', transcript)
        delete.setShortcuts(['Ctrl+D', 'Del'])
        delete.triggered.connect(self._delete_triggered)
        self.delete = delete
        transcript.addAction(delete)

        a = QAction('', self)
        a.setSeparator(True)
        transcript.addAction(a)

        reset = QAction('Reset minutes', transcript)
        reset.setShortcuts(['Ctrl+R'])
        reset.triggered.connect(self._reset_triggered)
        self.reset = reset
        transcript.addAction(reset)

        resetp = QAction('Reset problems', transcript)
        resetp.setShortcuts(['Ctrl+R'])
        resetp.triggered.connect(self._resetp_triggered)
        self.resetp = resetp
        transcript.addAction(resetp)

        a = QAction('', self)
        a.setSeparator(True)
        transcript.addAction(a)

        expand = QAction('Expand speakers', transcript)
        expand.setShortcuts(['Ctrl+E'])
        expand.triggered.connect(self._expand_triggered)
        self.expand = expand
        transcript.addAction(expand)

        self.setLayout(layout)
        edit.setChecked(False)

    
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
        self.insert.setEnabled(s)
        self.delete.setEnabled(s)
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
            self.reset.setEnabled(len(selected_rows) > 0)
            self.resetp.setEnabled(len(selected_rows) > 0)
            self.delete.setEnabled(len(selected_rows) > 0)

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
        self.model.insertRow(r, nr)

        self.transcript.selectRow(r)
        #self.transcript.setCurrentIndex(self.model.index(r, 1))
        #self.transcript.edit(self.model.index(r,1))

    @Slot()
    def _reset_triggered(self):
        self.annotation.set_minute()

    @Slot()
    def _resetp_triggered(self):
        self.annotation.set_problem()

    @Slot()
    def _delete_triggered(self):
        r = list(set([x.row() for x in self.transcript.selectionModel()]))
        self.model.removeRows(r[0], len(r))
        
    @Slot()
    def _transcript_changed(self):
        t = self.transcript_ver.currentText()
        self.annotation.open_transcript(t)