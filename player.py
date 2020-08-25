import os
import io
import math

from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QTableView, QCheckBox, QMenu, QAbstractItemView, QSizePolicy, QAction, QPlainTextEdit, QFormLayout, QTimeEdit, QDoubleSpinBox, QToolButton
from PySide2.QtCore import QItemSelectionModel, Slot
from PySide2.QtGui import QKeySequence
from PySide2 import QtWidgets
from PySide2.QtCore import Qt, QPoint, QModelIndex, Signal, QTime
from PySide2 import QtGui

from clickslider import ClickSlider
from recording import Recording

class Player(QWidget):
    was_playing = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._gui()

    def _gui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        slider_layout = QHBoxLayout()
        layout.addLayout(slider_layout)

        slider = ClickSlider(self)
        slider.mouse_pressed.connect(self._slider_pressed)
        slider.mouse_released.connect(self._slider_released)
        slider.setOrientation(Qt.Horizontal)
        slider.valueChanged.connect(self._slider_changed)
        slider_layout.addWidget(slider)
        self.slider = slider

        max_time = QLabel(self)
        self.max_time = max_time
        max_time.setText('--:--')
        slider_layout.addWidget(max_time)

        form = QFormLayout()
        layout.addLayout(form)

        time = QTimeEdit(self)
        time.setDisplayFormat('mm:ss.zzz')
        time.setAlignment(Qt.AlignRight)
        time.timeChanged.connect(self._edit_time_changed)
        self.time = time
        form.addRow(QLabel('Time', self),time)

        speed = QDoubleSpinBox(self)
        speed.setMinimum(0.1)
        speed.setMaximum(2.0)
        speed.setSingleStep(0.1)
        speed.setValue(1)
        speed.setAlignment(Qt.AlignRight)
        self.speed = speed
        speed.valueChanged.connect(self._speed_changed)
        form.addRow(QLabel('Speed', self), speed)

        playback = QHBoxLayout()
        layout.addLayout(playback)

        back_fast = QToolButton(self)
        playback.addWidget(back_fast)
        abf = QAction('<<', back_fast)
        abf.setShortcut(QKeySequence(Qt.Key_F1))
        abf.triggered.connect(self.back_fast)
        back_fast.setDefaultAction(abf)

        back = QToolButton(self)
        playback.addWidget(back)
        ab = QAction('<', back)
        ab.setShortcut(QKeySequence(Qt.Key_F2))
        ab.triggered.connect(self.back)
        back.setDefaultAction(ab)

        play = QToolButton(self)
        playback.addWidget(play)
        self.play_button = play
        play.setCheckable(True)
        play.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ap = QAction('Play', play)
        ap.setShortcut(QKeySequence(Qt.Key_F5))
        ap.triggered.connect(self.play)
        play.setDefaultAction(ap)

        forward = QToolButton(self)
        playback.addWidget(forward)
        af = QAction('>', forward)
        af.setShortcut(QKeySequence(Qt.Key_F3))
        af.triggered.connect(self.forward)
        forward.setDefaultAction(af)

        forward_fast = QToolButton(self)
        playback.addWidget(forward_fast)
        aff = QAction('>>', forward_fast)
        aff.setShortcut(QKeySequence(Qt.Key_F4))
        aff.triggered.connect(self.forward_fast)
        forward_fast.setDefaultAction(aff)

        speed_up = QAction('Speed up', forward_fast)
        speed_up.setShortcut(QKeySequence(Qt.Key_F7))
        speed_up.triggered.connect(self.speed.stepUp)

        speed_down = QAction('Speed down', forward_fast)
        speed_down.setShortcut(QKeySequence(Qt.Key_F6))
        speed_down.triggered.connect(self.speed.stepDown)
        
        self.utils = [
            slider,
            back_fast,
            back,
            play,
            forward,
            forward_fast,
            time,
            speed
        ]
        self.playback_actions = [abf, ab, ap, af, aff, speed_down, speed_up]
        self.set_enabled_utils(False)

        recording = Recording()
        self.recording = recording
        recording.time_changed.connect(self._time_changed)
        recording.playing_changed.connect(self._playing_changed)

        self.prevent = False

    def from_msecs(self, msecs):
        return QTime(0,0).addMSecs(msecs)

    @Slot(int)
    def _time_changed(self, time):
        self.time.setTime(self.from_msecs(time))
        self.slider.setValue(time)

    @Slot(bool)
    def _playing_changed(self, is_playing):
        self.play_button.setText('Stop' if is_playing else "Play")

    @Slot()
    def _speed_changed(self):
        self.recording.change_speed(self.speed.value())

    def is_playing(self):
        return self.recording.is_playing()

    @Slot()
    def _edit_time_changed(self):    
        msec = QTime(0,0).msecsTo(self.time.time())
        if not self.prevent:
            self.recording.set_time(msec)

    @Slot()
    def _slider_pressed(self):
        self.was_playing = self.recording.is_playing()
        self.recording.stop()

    @Slot()
    def _slider_released(self):
        msec = self.slider.value()
        self.recording.set_time(msec)
        if self.was_playing:
            self.recording.play()
            self.was_playing = False

    @Slot()
    def _slider_changed(self):
        self.prevent = True
        self.time.setTime(self.from_msecs(self.slider.value()))
        self.prevent = False

    @Slot()
    def back_fast(self):
        self.recording.change_time(-2000)

    @Slot()
    def back(self):
        self.recording.change_time(-1000)

    @Slot()
    def play(self):
        if self.is_playing():
            self.recording.stop()
        else:
            self.recording.play()

    @Slot()
    def forward(self):
        self.recording.change_time(1000)

    @Slot()
    def forward_fast(self):
        self.recording.change_time(2000)

    def set_enabled_utils(self, val):
        for u in self.playback_actions:
            u.setEnabled(val)
        for u in self.utils:
            u.setEnabled(val)

    def open_audio(self, file):
        self.file = file
        self.recording.open_file(file)
        
        self.slider.setMaximum(self.recording.duration)
        self.slider.setValue(0)

        t = QTime(0,0).addMSecs(self.recording.duration)
        self.time.setMaximumTime(t)
        self.max_time.setText('{:02d}:{:02d}'.format(
            t.minute(),
            t.second()
        ))

        self.set_enabled_utils(True)
