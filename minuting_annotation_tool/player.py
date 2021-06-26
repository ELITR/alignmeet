import time

try:
    import vlc
    has_vlc = True
except:
    has_vlc = False


from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy, QAction, QFormLayout, QTimeEdit, QDoubleSpinBox, QToolButton
from PySide2.QtCore import Slot
from PySide2.QtGui import QKeySequence
from PySide2.QtCore import Qt, QTime, QTimer

from .clickslider import ClickSlider

class Player(QWidget):
    was_playing = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._gui()
        self.file = None

    def _gui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        slider_layout = QHBoxLayout()
        layout.addLayout(slider_layout)

        slider = ClickSlider(self)
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

        self.prevent = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.start(1)
        self.player = None

    @Slot()
    def _update(self):
        if self.player is not None:
            self.prevent = True
            self.slider.setValue(self.player.get_position() * 100)
            msec = self.player.get_time()
            self.time.setTime(QTime.fromMSecsSinceStartOfDay(msec))
            self.prevent = False

    @Slot()
    def _speed_changed(self):
        if self.player is not None:
            self.player.set_rate(self.speed.value())

    def is_playing(self):
        if self.player is not None:
            return self.player.is_playing()

    @Slot()
    def _edit_time_changed(self):    
        msec = QTime(0,0).msecsTo(self.time.time())
        if self.player is not None and not self.prevent:
            self.player.set_time(msec)

    @Slot()
    def _slider_changed(self):
        if self.player is not None and not self.prevent:
            self.player.set_position(self.slider.value() / 100)
        

    @Slot()
    def back_fast(self):
        if self.player is not None:
            self.player.set_time(self.player.get_time() - 2000)

    @Slot()
    def back(self):
        if self.player is not None:
            self.player.set_time(self.player.get_time() - 1000)

    @Slot()
    def play(self):
        if self.player is None:
            self.player = self.media.player_new_from_media()

        if self.player.is_playing():
            self.player.pause()
            self.play_button.setText("Play")
        else:
            if not self.player.will_play():
                self.player = self.media.player_new_from_media()
            self.play_button.setText("Stop")
            self.player.play()

    @Slot()
    def forward(self):
        if self.player is not None:
            self.player.set_time(self.player.get_time() + 1000)

    @Slot()
    def forward_fast(self):
        if self.player is not None:
            self.player.set_time(self.player.get_time() + 2000)

    def set_enabled_utils(self, val = True):
        val = val if self.is_valid() else False
        for u in self.playback_actions:
            u.setEnabled(val)
        for u in self.utils:
            u.setEnabled(val)

    def open_audio(self, file):
        if not has_vlc:
            return False
        self.media = None
        self.player = None
        if file is None:
            self.setVisible(False)
            return
        self.file = file
        media = vlc.Media(file)
        media.parse_with_options(parse_flag=vlc.MediaParseFlag.local,timeout=100000)
        
        self.slider.setMaximum(100)
        self.slider.setValue(0)

        t = QTime.fromMSecsSinceStartOfDay(media.get_duration())
        self.time.setMaximumTime(t)
        self.max_time.setText(t.toString("h:m:s"))

        self.media = media
        self.player = media.player_new_from_media()
        
        self.set_enabled_utils()
        self.setVisible()

        return self.is_valid()


    def is_valid(self):
        try:
            return has_vlc and self.media is not None
        except:
            return False

    def setVisible(self, visible = True):
        if self.is_valid():
            super().setVisible(visible)
        else:
            super().setVisible(False)

