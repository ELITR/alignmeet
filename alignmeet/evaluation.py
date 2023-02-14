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

        adq_layout = QVBoxLayout()
        adq_layout.addWidget(QLabel('Document-level adequacy'))
        adequacy = QDoubleSpinBox(self)
        adequacy.setMinimum(1)
        adequacy.setMaximum(5)
        adq_layout.addWidget(adequacy)
        
        gram_layout = QVBoxLayout()
        gram_layout.addWidget(QLabel('grammaticality'))
        grammaticality = QDoubleSpinBox(self)
        grammaticality.setMinimum(1)
        grammaticality.setMaximum(5)
        gram_layout.addWidget(grammaticality)
        
        fluen_layout = QVBoxLayout()
        fluen_layout.addWidget(QLabel('fluency'))
        fluency = QDoubleSpinBox(self)
        fluency.setMinimum(1)
        fluency.setMaximum(5)
        fluen_layout.addWidget(fluency)
        
        relev_layout = QVBoxLayout()
        relev_layout.addWidget(QLabel('relevace'))
        relevance = QDoubleSpinBox(self)
        relevance.setMinimum(1)
        relevance.setMaximum(5)
        relev_layout.addWidget(relevance)
        
        slider_layout.addLayout(adq_layout)
        slider_layout.addLayout(gram_layout)
        slider_layout.addLayout(fluen_layout)
        slider_layout.addLayout(relev_layout)
        

        self.items = [
            adequacy,
            grammaticality,
            fluency,
            relevance
        ]

        for item in self.items:
            item.valueChanged.connect(self.evaluation_changed)


    def evaluation_changed(self,val):
        if self.prevent:
            return
        self.prevent = True
        self.annotation._adequacy = self.items[0].value()
        self.annotation._grammaticality = self.items[1].value()
        self.annotation._fluency = self.items[2].value()
        self.annotation._relevance= self.items[3].value()

        self.annotation.modified = True
        self.prevent = False

    @Slot(bool)
    def _set_values(self, m=True):
        if self.prevent:
            return
        self.prevent = True
        for v, item in zip([self.annotation._adequacy, self.annotation._grammaticality, self.annotation._fluency, self.annotation._relevance], self.items):
            item.setValue(v)
        self.prevent = False

    def open_evaluation(self, annotation):
        state = annotation.modified
        self.annotation = annotation
        self._set_values()
        annotation.modified = state
        annotation.modified_changed.connect(self._set_values)





    