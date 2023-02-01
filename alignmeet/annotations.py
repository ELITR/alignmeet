import os
import io
import glob

import subprocess
from subprocess import Popen

from PySide2.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QFileDialog, QMessageBox, QSplitter, QSizePolicy, QVBoxLayout, QProgressDialog, QAction, QToolBar, QDialog, QDialogButtonBox, QLabel, QLineEdit
from PySide2.QtCore import Slot, Qt, QSettings, Signal, QRunnable, QThreadPool
from PySide2.QtGui import QIcon

from .transcripts.transcripts import Transcripts
from .minutes.minutes import Minutes
from .player import Player
from .annotation import Annotation
from .problems import Problems
from .settings import Settings
from .evaluation import Evaluation
from .autoalign import Aligner, Embedder

class EmbedWorker(QRunnable):
        def __init__(self, annotation):
            super().__init__()
            self.annotation = annotation
            self.finished = Signal()
            
        @Slot()
        def run(self):
            e = Embedder()
            tr_embeds = []
            min_embeds = []
            for tr in self.annotation._das:
                tr_embeds.append(e.embed(tr))
            self.annotation.tr_embeds = tr_embeds
            for min in self.annotation._minutes:
                min_embeds.append(e.embed(min))
            self.annotation.min_embeds = min_embeds
            self.finished.emit()
            

class Annotations(QMainWindow):
    # main app window class 
    # creates menus and widgets, puts them in layout
    # has slots for opening folder/repo, saving
    # shows discard dialog box

    def __init__(self, *args, **kwargs):
        super(Annotations, self).__init__(*args, **kwargs)

        self.setWindowTitle("Annotations")
        self.folder = None
        self._gui_setup()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.is_git = False
        self.new_problem = ''
        self.embed_running = False

    def _gui_setup(self):
        layout = QHBoxLayout()

        splitter = QSplitter(Qt.Horizontal)
        panel_right = QWidget(self)
        layout.addWidget(splitter)

        annotation = Annotation()
        self.annotation = annotation
        self.annotation.undo_stack.canRedoChanged.connect(self._redo_toggle)
        self.annotation.undo_stack.canUndoChanged.connect(self._undo_toggle)

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

        problems = Problems(annotation, self)
        problems.setEnabled(False)
        problems.problem_selected.connect(self.annotation.set_problem)
        problems.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.problems = problems
        annotation.problems_chaged.connect(problems.refresh)
        
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

        # create all menu and toolbar actions
        self.newAction              = self._createAction('&New', 'Ctrl+n', self.new)
        self.openMeetingAction      = self._createAction('&Open meeting', 'Ctrl+o', self.open_existing)
        self.openRepositoryAction   = self._createAction('&Open repository', 'Ctrl+g', self.open_repository)
        self.evalModeAction         = self._createAction('Evaluation mode', 'Ctrl+e', self.set_evaluation_mode)
        self.evalModeAction.setCheckable(True)
        self.saveAction             = self._createAction('&Save', 'Ctrl+s', self.save)
        self.saveAction.setEnabled(False)
        self.settingsAction         = self._createAction('S&ettings', 'Ctrl++', lambda : Settings(self).exec_())
        self.closeAction            = self._createAction('&Close', 'Alt+c', self.close)
        self.undoAction             = self._createAction('&Undo', 'Ctrl+z', self.annotation.undo)
        self.undoAction.setIcon(QIcon("alignmeet/icons/arrow-return-180-left.png"))
        self.undoAction.setEnabled(False)
        self.annotation.undo_toggle.connect(self._undo_toggle)
        self.redoAction             = self._createAction('&Redo', 'Ctrl+y', self.annotation.redo)
        self.redoAction.setIcon(QIcon("alignmeet/icons/arrow-return.png"))
        self.redoAction.setEnabled(False)
        self.annotation.redo_toggle.connect(self._redo_toggle)
        self.editHistoryAction      = self._createAction('Show edit &history', 'Alt+h', self.annotation.show_edit_history)
        self.openAudioAction        = self._createAction('&Open audio', 'Alt+o', self._open_audio)
        self.autoalignAction        = self._createAction('&Autoalign', 'Alt+a', self._autoalign)
        self.autoalignAction.setEnabled(False)
        self.aaSettingsAction       = self._createAction('&Settings...', '', self._aaSettings)
        self.aaFinalizeAction       = self._createAction('&Finalize', 'Alt+f', self._aaFinalize)
        self.aaFinalizeAction.setEnabled(False)
        self.aaFinalizeAllAction    = self._createAction('Fi&nalize all', '', self._aaFinalizeAll)
        self.aaFinalizeAllAction.setEnabled(False)
        
        # create menu bar
        menu = self.menuBar()

        file_menu = menu.addMenu('&File')
        file_menu.addAction(self.newAction)
        file_menu.addAction(self.openMeetingAction)
        file_menu.addAction(self.openRepositoryAction)
        file_menu.addSeparator()

        file_menu.addAction(self.evalModeAction)
        file_menu.addSeparator()

        file_menu.addAction(self.saveAction)
        file_menu.addSeparator()

        file_menu.addAction(self.settingsAction)
        file_menu.addSeparator()

        file_menu.addAction(self.closeAction)

        edit_menu = menu.addMenu('&Edit')
        edit_menu.addAction(self.undoAction)
        edit_menu.addAction(self.redoAction)
        edit_menu.addAction(self.editHistoryAction)

        edit_menu.addSeparator()

        edit_menu.addAction(self.problems.addProblemAction)
        edit_menu.addAction(self.problems.refreshProblemsAction)

        edit_menu.addSeparator()

        transcript_edit_menu = edit_menu.addMenu('&Transcript')

        transcript_edit_menu.addAction(self.minutes.insertingAction)
        transcript_edit_menu.addAction(self.minutes.deleteAction)
        transcript_edit_menu.addAction(self.minutes.joinDownAction)
        transcript_edit_menu.addAction(self.minutes.joinUpAction)
        transcript_edit_menu.addAction(self.minutes.splitAction)

        minutes_edit_menu = edit_menu.addMenu('&Minutes')

        minutes_edit_menu.addAction(self.transcripts.insertingAction)
        minutes_edit_menu.addAction(self.transcripts.deleteAction)
        minutes_edit_menu.addAction(self.transcripts.joinDownAction)
        minutes_edit_menu.addAction(self.transcripts.joinUpAction)
        minutes_edit_menu.addAction(self.transcripts.splitAction)

        playback_menu = menu.addMenu('&Playback')
        playback_menu.addAction(self.openAudioAction)
        playback_menu.addSeparator()
        playback_menu.addActions(player.playback_actions)
        
        autoalign_menu = menu.addMenu('&Autoalign')
        #autoalign_menu.addAction(self.autoalignAction)
        #autoalign_menu.addAction(self.aaSettings)
        #autoalign_menu.addSeparator()
        autoalign_menu.addAction(self.aaFinalizeAction)
        autoalign_menu.addAction(self.aaFinalizeAllAction)        

        # Add toolbar (with undo redo, edit mode toggle)
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(self.undoAction)
        toolbar.addAction(self.redoAction)
        toolbar.addSeparator()
        toolbar.addAction(self.evalModeAction)
        toolbar.addSeparator()
        toolbar.addAction(self.aaFinalizeAction)
        toolbar.addAction(self.aaFinalizeAllAction)
        self.toolbar = toolbar

        # Set up settings for saving layout upon close
        s = QSettings(self)
        self.splitter = splitter
        self.splitter_righ = splitter_right
        splitter.restoreState(s.value('splitter'))
        splitter_right.restoreState(s.value('splitter_righ'))
        self.restoreGeometry(s.value('window_geometry'))
        self.restoreState(s.value('window_state'))
        
        splitter_right.setStretchFactor(0, 10)
        splitter_right.setStretchFactor(1, 1)

    def _createAction(self, name : str, shortcut : str, connection):
        a = QAction(name)
        a.setShortcut(shortcut)
        a.triggered.connect(connection)
        return a

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
                self.saveAction.setEnabled(True)
                self.autoalignAction.setEnabled(True)
                self.aaFinalizeAction.setEnabled(True)
                self.aaFinalizeAllAction.setEnabled(True)
                self.problems.addProblemAction.setEnabled(True)
                self.problems.refreshProblemsAction.setEnabled(True)
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
                self.saveAction.setEnabled(True)
                self.autoalignAction.setEnabled(True)
                self.aaFinalizeAction.setEnabled(True)
                self.aaFinalizeAllAction.setEnabled(True)
                self.problems.addProblemAction.setEnabled(True)
                self.problems.refreshProblemsAction.setEnabled(True)
                
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

            process = Popen(["git", "push"], cwd=self.annotation._path, stdout=subprocess.PIPE)
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

    @Slot(bool)
    def _undo_toggle(self, value):
        self.undoAction.setEnabled(value)

    @Slot(bool)
    def _redo_toggle(self, value):
        self.redoAction.setEnabled(value)

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
                    self.annotation.undo_view.close()
                elif QMessageBox.Cancel == msg.result():
                    event.ignore()
                self.annotation.undo_view.close()
                return

        self.annotation.undo_view.close()
        return super().closeEvent(event)
    
    @Slot()
    def _autoalign(self):
        pass
    
    @Slot()
    def _aaSettings(self):
        pass
    
    @Slot()
    def _aaSettings(self):
        pass
    
    @Slot()
    def _aaFinalize(self):
        self.annotation.finalize()

    @Slot()
    def _aaFinalizeAll(self):
        self.annotation.finalizeAll()
