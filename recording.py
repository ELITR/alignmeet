from PySide2.QtCore import QObject, Signal, Slot, QTimer, QTime
import simpleaudio as sa
import numpy as np
#import soundfile as sf
import sox

class Recording(QObject):
    time_changed = Signal(int)
    playing_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.time_changed_firing = False
        self.timer = None
        self.data_original = []
        self.data = []
        self.speed = 1.0
        self.time = 0
        self.buff = None

        self.samplerate = None
        self.duration = None
        self.channels = None

    def open_file(self, file):
        t = sox.Transformer()
        self.data_original = t.build_array(input_filepath=file)
        self.samplerate = int(sox.file_info.sample_rate(file))
        self.duration = sox.file_info.duration(file) * 1000
        self.channels = sox.file_info.channels(file)
        self.apply_effects()

    def play(self):
        self.stop()

        f = self.samplerate * self.time / self.speed / 1000
        f = int(f)
        audio = self.data[f:]

        self.buff = sa.play_buffer(
            audio,
            num_channels=self.channels,
            bytes_per_sample=2,
            sample_rate=int(self.samplerate)
        )

        self.play_start = QTime.currentTime()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.start(10)
        self.playing_changed.emit(True)

    def stop(self):
        if self.timer is not None:
            self.timer.stop()
        if self.buff is not None:
            self.buff.stop()
        self.playing_changed.emit(False)
            
    def is_playing(self):
        return self.buff is not None and self.buff.is_playing()

    def apply_effects(self):
        if abs(self.speed - 1) > 1e-5:
            t = sox.Transformer()
            t.tempo(self.speed, audio_type='s', quick=True)
            audio = t.build_array(input_array=self.data_original, sample_rate_in=self.samplerate)
            audio = np.array(audio, dtype=np.float)
        else:
            audio = np.array(self.data_original, dtype=np.float)
        audio *= 32767 / np.max(np.abs(audio))
        audio = audio.astype(np.int16)
        self.data = audio

    def set_time(self, time):
        if self.time_changed_firing:
            return
        time = min(time, self.duration)
        self.time = max(time, 0)
        self.restart()

        self._fire_time_update()

    def change_time(self, delta):
        self.set_time(self.time + delta)

    def change_speed(self, speed):
        self.speed = speed
        self.apply_effects()
        self.restart()

    def restart(self):
        if self.is_playing():
            self.stop()
            self.play()

    def _fire_time_update(self):
        self.time_changed_firing = True
        self.time_changed.emit(self.time)
        self.time_changed_firing = False

    @Slot()
    def _update(self):
        if self.buff.is_playing():
            self.time += int(self.play_start.msecsTo(QTime.currentTime())*self.speed)
            self.play_start = QTime.currentTime()
        else:
            self.timer.stop()
            self.time = 0
            self.stop()

        self._fire_time_update()
