from PySide2.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QListWidget, QGroupBox
from PySide2.QtCore import Signal

PROBLEMS = [
        'Organizational',
        'Speech incomprehensible',
        'See separate comment',
        'Small talk',
        'Censored'
    ]

class Problems(QWidget):
    problem_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._gui()

    def _gui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        group = QGroupBox('Other', self)
        group.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(group)

        layout = QVBoxLayout()
        group.setLayout(layout)

        problems = List(self)
        problems.problem_selected.connect(self.problem_selected)
        problems.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(problems, 0)
        
        for i in PROBLEMS:
            problems.addItem(i)

        problems.clearSelection()
        layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        layout.update()

class List(QListWidget):
    problem_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def mouseDoubleClickEvent(self, QMouseEvent):
        items = self.selectedIndexes()
        if len(items) == 1:
            item = items[0].row()
            self.problem_selected.emit(item)
        return super().mouseDoubleClickEvent(QMouseEvent)