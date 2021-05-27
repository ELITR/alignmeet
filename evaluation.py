import os
import io
import math

from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QTableView, QCheckBox, QMenu, QAbstractItemView, QSizePolicy, QAction, QPlainTextEdit, QFormLayout, QTimeEdit, QDoubleSpinBox, QToolButton
from PySide2.QtCore import QItemSelectionModel, Slot
from PySide2.QtGui import QKeySequence
from PySide2 import QtWidgets
from PySide2.QtCore import Qt, QPoint, QModelIndex, Signal, QTime, QTimer
from PySide2 import QtGui

from clickslider import ClickSlider

class Evaluation(QWidget):
    was_playing = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.annotation = None
        self._gui()
        self.setEnabled(False)
        self.prevent = False

    def _gui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        slider_layout = QHBoxLayout()
        layout.addLayout(slider_layout)

        slider_layout.addWidget(QLabel('Aadequacy'))
        adequacy = QDoubleSpinBox(self)
        adequacy.setMinimum(1)
        adequacy.setMaximum(5)
        self.adequacy = adequacy
        slider_layout.addWidget(adequacy)


        slider_layout.addWidget(QLabel('Relevance'))
        relevance = QDoubleSpinBox(self)
        relevance.setMinimum(1)
        relevance.setMaximum(5)
        self.relevance = relevance
        slider_layout.addWidget(relevance)
        
        slider_layout.addWidget(QLabel('Coverage'))
        coverage = QDoubleSpinBox(self)
        coverage.setMinimum(1)
        coverage.setMaximum(5)
        self.coverage = coverage
        slider_layout.addWidget(coverage)

        
        slider_layout = QHBoxLayout()
        layout.addLayout(slider_layout)
        
        slider_layout.addWidget(QLabel('Readability'))
        readability = QDoubleSpinBox(self)
        readability.setMinimum(1)
        readability.setMaximum(5)
        self.readability = readability
        slider_layout.addWidget(readability)
        
        slider_layout.addWidget(QLabel('Grammaticality'))
        grammaticality = QDoubleSpinBox(self)
        grammaticality.setMinimum(1)
        grammaticality.setMaximum(5)
        self.grammaticality = grammaticality
        slider_layout.addWidget(grammaticality)

        slider_layout.addWidget(QLabel('Total'))
        total = QLabel('0')
        self.total = total
        slider_layout.addWidget(total)

        self.items = [
            adequacy,
            relevance,
            coverage,
            readability,
            grammaticality,
        ]

        for item in self.items:
            item.valueChanged.connect(self.evaluation_changed)


    def evaluation_changed(self,val):
        if self.prevent:
            return
        self.prevent = True
        self.annotation._evaluation = [
            item.value() for item in self.items
        ]
        total = 0.2 * self.adequacy.value() \
            + 0.2 * self.relevance.value() \
            + 0.2 * self.coverage.value() \
            + 0.2 * self.readability.value() \
            + 0.2 * self.grammaticality.value()
        self.annotation._evaluation.append(total)
        self.total.setText("{:.2f}".format(total))
        self.annotation.modified = True
        self.prevent = False

    @Slot(bool)
    def _set_values(self, m=True):
        if self.prevent:
            return
        self.prevent = True
        for v, item in zip(self.annotation._evaluation, self.items):
            item.setValue(v)
        self.prevent = False

    def open_evaluation(self, annotation):
        state = annotation.modified
        self.annotation = annotation
        self._set_values()
        annotation.modified = state
        annotation.modified_changed.connect(self._set_values)





    