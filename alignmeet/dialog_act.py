from PySide2.QtWidgets import QLabel, QHBoxLayout, QWidget
from PySide2 import QtGui
from PySide2.QtWidgets import QSizePolicy

class DialogAct(QWidget):
    def __init__(self, *args, **kwargs):
        super(DialogAct, self).__init__(*args, **kwargs)
        self._gui_setup()
        self.set_data(['FS'], ('FS', 'foo transcript'))
        self._update_gui()

    def set_data(self, speakers, da):
        self.speakers = speakers
        self.da = da
        self._update_gui()

    def _update_gui(self):
        self.speaker.setText(self.da[0])
        self.transcript.setText(self.da[1])


    def _gui_setup(self):
        layout = QHBoxLayout()

        speaker = QLabel()
        font = QtGui.QFont()
        font.setBold(True)
        speaker.setFont(font)
        speaker.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.speaker = speaker
        layout.addWidget(speaker)

        transcript = QLabel()
        speaker.setFont(font)
        transcript.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.transcript = transcript
        layout.addWidget(transcript)

        self.setLayout(layout)
