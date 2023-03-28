from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QListWidget, QLabel, QToolBar, QAction, QLineEdit, QDialog, QDialogButtonBox
from PySide2.QtCore import Signal, Slot, Qt
from PySide2.QtGui import QIcon
from .annotation import Annotation

import os

PROBLEMS = [
        'Organizational',
        'Speech incomprehensible',
        'See separate comment',
        'Small talk',
        'Censored'
    ]

class Problems(QWidget):
    problem_selected = Signal(object)

    def __init__(self, annotation : Annotation, parent=None):
        super().__init__(parent=parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.annotation = annotation
        self._gui()

    def _gui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        line_layout = QHBoxLayout()
        label = QLabel('Remarks')
        line_layout.addWidget(label)

        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        line_layout.addWidget(empty)

        self.toolbar = QToolBar("Problems toolbar")
        self.toolbar.setMovable(False)
        line_layout.addWidget(self.toolbar)

        self.addProblemAction = QAction('&Add problem')
        self.addProblemAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"icons/plus.png")))
        self.addProblemAction.setEnabled(False)
        self.addProblemAction.triggered.connect(self.new_problem)
        self.toolbar.addAction(self.addProblemAction)

        self.refreshProblemsAction = QAction('&Refresh problems')
        self.refreshProblemsAction.setShortcut('ctrl+r')
        self.refreshProblemsAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"icons/arrow-circle-315.png")))
        self.refreshProblemsAction.setEnabled(False)
        self.refreshProblemsAction.triggered.connect(self.refresh)
        self.toolbar.addAction(self.refreshProblemsAction)

        layout.addLayout(line_layout)

        problems = List(self)
        for i in PROBLEMS:
            problems.addItem(i)
        for tl in self.annotation._das:
            if isinstance(tl.problem, str):
                problems.addItem(tl.problem)
        problems.problem_selected.connect(self.problem_selected)
        problems.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(problems)
        self.problems = problems

        problems.clearSelection()

    @Slot()
    def refresh(self):
        self.problems.clear()
        all_problems = []
        for i in PROBLEMS:
            self.problems.addItem(i)
            all_problems.append(i)
        for tl in self.annotation._das:
            if isinstance(tl.problem, str) and not tl.problem in all_problems:
                self.problems.addItem(tl.problem)
                all_problems.append(tl.problem)

    @Slot(str)
    def add_problem(self, problem):
        all_problems = [i.text() for i in self.problems.findItems('*', Qt.MatchWildcard)]
        if not problem in all_problems:
            self.problems.addItem(problem)

    def _set_temp_problem(self, text):
        self.temp_problem = text

    def new_problem(self):
        self._set_temp_problem('')
        dlg = ProblemDialog()
        dlg.textbox.textChanged.connect(self._set_temp_problem)
        if dlg.exec_():
            self.add_problem(self.temp_problem)

class List(QListWidget):
    problem_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def mouseDoubleClickEvent(self, QMouseEvent):
        items = self.selectedIndexes()
        if len(items) == 1:
            item = items[0].row()
            if item > len(PROBLEMS) - 1:
                item = items[0].data()
            self.problem_selected.emit(item)
        return super().mouseDoubleClickEvent(QMouseEvent)

class ProblemDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add problem")
        layout = QVBoxLayout()

        self.label = QLabel("Enter problem name:")
        layout.addWidget(self.label)

        self.textbox = QLineEdit(self)
        layout.addWidget(self.textbox)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.rejected.connect(self.reject)
        self.buttons.accepted.connect(self.accept)

        layout.addWidget(self.buttons)

        self.setLayout(layout)

