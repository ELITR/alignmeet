import os
import io
import glob

import subprocess
from subprocess import Popen

from PySide2.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QFileDialog, QMessageBox, QSplitter, QSizePolicy, QVBoxLayout, QProgressDialog
from PySide2.QtCore import Slot, Qt, QSettings

from .transcripts.transcripts import Transcripts
from .minutes.minutes import Minutes
from .player import Player
from .annotation import Annotation
from .problems import Problems
from .settings import Settings
from .evaluation import Evaluation

class Annotations(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(Annotations, self).__init__(*args, **kwargs)

        self.setWindowTitle("Annotations")
        self.folder = None
        self._gui_setup()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.is_git = False

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
        
        a = file_menu.addAction('&Open repository')
        a.setShortcut('Ctrl+g')
        a.triggered.connect(self.open_repository)

        file_menu.addSeparator()

        a = file_menu.addAction('Evaluation mode')
        a.setCheckable(True)
        a.setShortcut('Ctrl+e')
        a.triggered.connect(self.set_evaluation_mode)

        file_menu.addSeparator()

        a = file_menu.addAction('&Save')
        a.setShortcut('Ctrl+s')
        a.triggered.connect(self.save)
        file_menu.addSeparator()

        a = file_menu.addAction('S&ettings')
        a.setShortcut('Ctrl++')
        a.triggered.connect(lambda : Settings(self).exec_())
        file_menu.addSeparator()

        a = file_menu.addAction('&Close')
        a.setShortcut('Alt+c')
        a.triggered.connect(self.close)

        playback_menu = menu.addMenu('&Playback')
        a = playback_menu.addAction('&Open audio')
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
                self.annotation.modified = False
                return True
            else:
                return False
        return False

    @Slot()
    def new(self):
        self.open_existing(True)

    @Slot()
    def open_repository(self):
        s = QSettings(self)
        s.setValue('repo_location', s.value('repo_location', os.path.abspath('./repository')))
        path = os.path.abspath(s.value('repo_location', './repository'))
        repo = s.value('repository', '')
        repo_name = repo.split('/')[-1].split('.')[0] if repo.endswith('.git') else ''
        user = s.value('user', '')
        token = s.value('token', '')
        
        if len(repo) == 0 or len(user) == 0 or len(token) == 0 or len(repo_name) == 0:
            msg = QMessageBox()
            msg.setText('Invalid repository settings!\nGo to File->Settings and set Repository, User and Token values')
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.exec_()
            return

        
        if not os.path.exists(path):
            os.mkdir(path)

        repo_path = os.path.join(path,repo_name)

        progress = QProgressDialog()
        progress.setModal(True)
        progress.setAutoClose(True)
        progress.setWindowTitle('Opening repository')
        progress.show()
        progress.setValue(0)
        progress.setLabelText('Cloning repo (might take a while)... ')
        QApplication.processEvents()

        if not os.path.exists(repo_path):
            repo = repo.replace('https://', '')
            url = f'https://{user}:{token}@{repo}'
            process = Popen(["git", "clone", url], cwd=path, stdout=subprocess.PIPE)

            process.communicate()
            if process.returncode > 0:
                msg = QMessageBox()
                msg.setText('Error while cloning repository')
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Error")
                msg.exec_()
                return
        progress.setValue(50)
        progress.setLabelText('Updating repo... ')
        QApplication.processEvents()

        process = Popen(["git", "pull"], cwd=repo_path, stdout=subprocess.PIPE)
        process.communicate()
        if process.returncode > 0:
            msg = QMessageBox()
            msg.setText('Error while updating repository')
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.exec_()
            return
        progress.setValue(100)
        QApplication.processEvents()

        if self.open_existing(restrict=repo_path):
            self.is_git = True


    @Slot()
    def set_evaluation_mode(self, evaluation):
        self.minutes.set_evaluation_mode(evaluation)
        self.transcripts.set_evaluation_mode(evaluation)
        self.player.setVisible(not evaluation)
        self.evaluation.setVisible(evaluation)

    @Slot()
    def open_existing(self, create=False, restrict=None):
        if self.annotation.modified and not self._discard_dialog():
            return
        dlg = QFileDialog(self, 'Select directory')
        if restrict:
            dlg.setDirectory(restrict)
            def check(d, restrict):
                print(d)
                d = os.path.normpath(d)
                restrict = os.path.normpath(restrict)
                if not d.startswith(restrict):
                    dlg.setDirectory(restrict)
            dlg.directoryEntered.connect(lambda t: check(t, restrict))
        dlg.setOptions(QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog)
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
                exts = ['wav', 'mp3', 'flac', 'mp4']
                self.player.open_audio(None)
                for e in exts:
                    for f in glob.glob(os.path.normpath(os.path.join(path, '*.' + e))):
                        if os.path.isfile(os.path.normpath(os.path.join(path, f))):
                            if self.player.open_audio(os.path.normpath(os.path.join(path, f))):
                                break
                self.is_git = False
                return True
            else:
                msg = QMessageBox()
                msg.setText('Invalid directory!')
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Error")
                msg.exec_()
        return False


    def _check_path(self, path):
        return True

    @Slot()
    def save(self):
        self.annotation.save()
        if self.is_git:
            s = QSettings(self)
            annotator = s.value('annotator', 'annonymous')

            progress = QProgressDialog()
            progress.setModal(True)
            progress.setAutoClose(True)
            progress.setWindowTitle('Saving repository')
            progress.setLabelText('')
            progress.show()
            progress.setValue(0)
            progress.setLabelText('Adding files... ')
            QApplication.processEvents()

            process = Popen(["git", "pull"], cwd=self.annotation._path, stdout=subprocess.PIPE)
            process.communicate()
            progress.setValue(100)
            QApplication.processEvents()

            process = Popen(["git", "add", "*"], cwd=self.annotation._path, stdout=subprocess.PIPE)
            process.communicate()
            progress.setLabelText('Commiting... ')
            progress.setValue(33)
            QApplication.processEvents()

            process = Popen(["git", "commit", "-m", annotator], cwd=self.annotation._path, stdout=subprocess.PIPE)
            process.communicate()
            progress.setValue(66)
            progress.setLabelText('Pushing to remote... ')
            QApplication.processEvents()

            process = Popen(["git", "push", "origin", "main"], cwd=self.annotation._path, stdout=subprocess.PIPE)
            process.communicate()
            progress.setValue(100)
            QApplication.processEvents()


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