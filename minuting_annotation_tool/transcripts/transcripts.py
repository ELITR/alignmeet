import re
from copy import copy

from PySide2.QtWidgets import QLineEdit, QPushButton, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QCheckBox, QAbstractItemView, QSizePolicy, QAction
from PySide2.QtCore import Qt, Slot
from PySide2 import QtWidgets
from ..transcripts.dialog_act_model import DAModel
from ..transcripts.speaker_editor import SpeakerEditor
from ..transcripts.dialog_act_editor import DialogActEditor
from ..transcripts.transcript import Transcript
from ..annotation import Annotation, DialogAct
from ..combobox import ComboBox

class Transcripts(QWidget):
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
        reset.setShortcuts(['Ctrl+m'])
        reset.triggered.connect(self._reset_triggered)
        self.reset = reset
        transcript.addAction(reset)

        resetp = QAction('Reset problems', transcript)
        resetp.setShortcuts(['Ctrl+p'])
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
        self._editation(not evaluation)

        if evaluation:
            self.edit.setChecked(False)
        self.edit.setEnabled(not evaluation)

    
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
            self.delete.setEnabled(len(selected_rows) > 0 and not self._evaluation_mode)
        self.reset.setEnabled(len(selected_rows) > 0 and not self._evaluation_mode)
        self.resetp.setEnabled(len(selected_rows) > 0 and not self._evaluation_mode)

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

        self.transcript.clearSelection()
        self.transcript.setCurrentIndex(self.model.index(r, 1))
        #self.transcript.edit(self.model.index(r,1))

    @Slot()
    def _reset_triggered(self):
        self.annotation.set_minute()

    @Slot()
    def _resetp_triggered(self):
        self.annotation.set_problem()

    @Slot()
    def _delete_triggered(self):
        r = list(set([x.row() for x in self.transcript.selectionModel().selectedRows()]))
        self.model.removeRows(r[0], len(r))
        
    @Slot()
    def _transcript_changed(self):
        t = self.transcript_ver.currentText()
        self.annotation.open_transcript(t)