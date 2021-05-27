import os
import io

from PySide2.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QFileDialog, QMessageBox, QSplitter, QSizePolicy, QVBoxLayout, QAction, QMenuBar
from PySide2.QtCore import Slot, Qt, QCoreApplication, QSettings
from PySide2.QtGui import QKeySequence

from transcripts.transcripts import Transcripts
from minutes.minutes import Minutes
from player import Player
from annotation import Annotation
from problems import Problems
from settings import Settings
from evaluation import Evaluation

class Annotations(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(Annotations, self).__init__(*args, **kwargs)

        self.setWindowTitle("Annotations")
        self.folder = None
        self._gui_setup()
        self.setAttribute(Qt.WA_DeleteOnClose)

    def _gui_setup(self):
        layout = QHBoxLayout()

        splitter = QSplitter(Qt.Horizontal)
        panel_right = QWidget(self)
        layout.addWidget(splitter)

        annotation = Annotation()
        self.annotation = annotation

        transcripts = Transcripts(annotation, self)
        transcripts.setDisabled(True)
        splitter.addWidget(transcripts)
        self.transcripts = transcripts
        splitter.addWidget(panel_right)
        l = QVBoxLayout()
        l.setContentsMargins(0,0,0,0) 
        panel_right.setLayout(l)
        panel_right = l

        minutes = Minutes(annotation, self)
        minutes.setDisabled(True)
        self.minutes = minutes

        problems = Problems(self)
        problems.setEnabled(False)
        problems.problem_selected.connect(self.annotation.set_problem)
        problems.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.problems = problems
        
        splitter_right = QSplitter(Qt.Vertical)
        splitter_right.addWidget(minutes)
        splitter_right.addWidget(problems)
        panel_right.addWidget(splitter_right)

        player = Player(self)
        player.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.player = player
        panel_right.addWidget(player)

        evaluation = Evaluation(self)
        evaluation.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.evaluation = evaluation
        panel_right.addWidget(evaluation)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        menu = self.menuBar()
        file_menu = menu.addMenu('&File')

        a = file_menu.addAction('&New')
        a.setShortcut('Ctrl+n')
        a.triggered.connect(self.new)

        a = file_menu.addAction('&Open existing')
        a.setShortcut('Ctrl+o')
        a.triggered.connect(self.open_existing)
        file_menu.addSeparator()

        a = file_menu.addAction('&Save')
        a.setShortcut('Ctrl+s')
        a.triggered.connect(self.save)
        file_menu.addSeparator()

        a = file_menu.addAction('S&ettings')
        a.setShortcut('Ctrl+e')
        a.triggered.connect(lambda : Settings(self).exec_())
        file_menu.addSeparator()

        a = file_menu.addAction('&Close')
        a.setShortcut('Alt+c')
        a.triggered.connect(self.close)

        playback_menu = menu.addMenu('&Playback')
        a = playback_menu.addAction('&Open audio')
        a.setShortcut('Ctrl+p')
        a.triggered.connect(self._open_audio)
        playback_menu.addSeparator()
        playback_menu.addActions(player.playback_actions)

        s = QSettings(self)
        self.splitter = splitter
        self.splitter_righ = splitter_right
        splitter.restoreState(s.value('splitter'))
        splitter_right.restoreState(s.value('splitter_righ'))
        self.restoreGeometry(s.value('window_geometry'))
        self.restoreState(s.value('window_state'))
        
        splitter_right.setStretchFactor(0, 10)
        splitter_right.setStretchFactor(1, 1)

    def _discard_dialog(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setText('Opened meeting was modified.\nDo you wish to discard the changes?')
        msg.setStandardButtons(QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        if msg.exec_():
            if QMessageBox.Save == msg.result():
                self.save()
                return True
            elif QMessageBox.Discard == msg.result():
                return True
            else:
                return False
        return False

    @Slot()
    def new(self):
        if not self.annotation.modified or self._discard_dialog():
            self.open_existing(True)

    @Slot()
    def open_existing(self, create=False):
        if self.annotation.modified and not self._discard_dialog():
            return
        dlg = QFileDialog(self, 'Select directory')
        dlg.setFileMode(dlg.DirectoryOnly)
        if dlg.exec_():
            path = dlg.selectedFiles()[0]
            if create:
                t = os.path.join(path, 'transcripts')
                t = os.path.normpath(t)
                os.mkdir(t)
                m = os.path.join(path, 'annotations')
                m = os.path.normpath(m)
                os.mkdir(m)
                m = os.path.join(path, 'minutes')
                m = os.path.normpath(m)
                os.mkdir(m)
                io.open(os.path.join(m,'minutes.txt'),'w').write('')
                io.open(os.path.join(t,'transcript.txt'),'w').write('')
            if self._check_path(path):
                self.annotation.set_path(path)
                self.transcripts.setEnabled(True)
                self.minutes.setEnabled(True)
                self.problems.setEnabled(True)
                self.evaluation.setEnabled(True)
                self.evaluation.open_evaluation(self.annotation)
                for f in os.listdir(path):
                    if os.path.isfile(os.path.normpath(os.path.join(path, f))):
                        self.player.open_audio(os.path.normpath(os.path.join(path, f)))
                        break
            else:
                msg = QMessageBox()
                msg.setText('Invalid directory!')
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Error")
                msg.exec_()

    def _check_path(self, path):
        return os.path.exists(os.path.normpath(os.path.join(path, 'transcripts')))

    @Slot()
    def save(self):
        self.annotation.save()

    @Slot()
    def _open_audio(self):
        dlg = QFileDialog(self, 'Select audio file')
        dlg.setFileMode(dlg.ExistingFile)
        #dlg.setMimeTypeFilters(['audio/wav', 'audio/aac', 'audio/mpeg', 'video/mpeg'])
        if dlg.exec_():
            if len(dlg.selectedFiles()) > 0 and os.path.exists(dlg.selectedFiles()[0]):
                file = dlg.selectedFiles()[0]
                self.player.open_audio(file)

    def closeEvent(self, event):
        s = QSettings(self)
        s.setValue('window_state', self.saveState())
        s.setValue('window_geometry', self.saveGeometry())
        s.setValue('splitter', self.splitter.saveState())
        s.setValue('splitter_geometry', self.splitter.saveGeometry())
        s.setValue('splitter_righ', self.splitter_righ.saveState())
        s.setValue('splitter_righ_geometry', self.splitter_righ.saveGeometry())

        if self.annotation.modified:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setText('Opened meeting was modified.\nDo you wish to discard the changes?')
            msg.setStandardButtons(QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Cancel)
            if msg.exec_():
                if QMessageBox.Save == msg.result():
                    self.save()
                elif QMessageBox.Cancel == msg.result():
                    event.ignore()
                return
        return super().closeEvent(event)