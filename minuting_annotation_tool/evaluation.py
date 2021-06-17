from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QDoubleSpinBox
from PySide2.QtCore import Slot

class Evaluation(QWidget):
    was_playing = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.annotation = None
        self._gui()
        self.setVisible(False)
        self.setEnabled(False)
        self.prevent = False

    def _gui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        slider_layout = QHBoxLayout()
        layout.addLayout(slider_layout)

        slider_layout.addWidget(QLabel('Document-level adequacy'))
        adequacy = QDoubleSpinBox(self)
        adequacy.setMinimum(1)
        adequacy.setMaximum(5)
        self.adequacy = adequacy
        slider_layout.addWidget(adequacy)

        self.items = [
            adequacy,
        ]

        for item in self.items:
            item.valueChanged.connect(self.evaluation_changed)


    def evaluation_changed(self,val):
        if self.prevent:
            return
        self.prevent = True
        self.annotation._document_level_adequacy = self.adequacy.value()

        self.annotation.modified = True
        self.prevent = False

    @Slot(bool)
    def _set_values(self, m=True):
        if self.prevent:
            return
        self.prevent = True
        for v, item in zip([self.annotation._document_level_adequacy,], self.items):
            item.setValue(v)
        self.prevent = False

    def open_evaluation(self, annotation):
        state = annotation.modified
        self.annotation = annotation
        self._set_values()
        annotation.modified = state
        annotation.modified_changed.connect(self._set_values)





    