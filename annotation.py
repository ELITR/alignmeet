from os import path, listdir
import re

from PySide2.QtCore import Qt, QPoint, QModelIndex, Signal, QObject
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QMessageBox

SEPARATOR = '^'
TRANSCRIPT_FOLDER = 'transcripts'
MINUTES_FOLDER = 'minutes'
ANNOTATIONS_FOLDER = 'annotations'

class Minute:
    max_id = -1
    def __init__(self, text = '', id = -1):
        super().__init__()
        if id == -1:
            id = Minute.max_id + 1
        self._id = id
        self.id = id
        self.text = text

    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        Minute.max_id = max(value, Minute.max_id)
        self._id = value

class DialogAct:
    speakers = set()
    def __init__(self,  text = '', speaker = '',start = -1, end = -1, minute : Minute = None, problem = None):
        self._speaker = speaker
        if speaker is None or len(speaker) < 1:
            for f in re.findall('^\s*\([a-zA-Z]+\)', text):
                speaker = f[1:-1]
                text = text.replace(f, '', 1)
                break
        self.speaker = speaker
        self.text = text
        self.minute = minute
        self.problem = problem
        self.start = int(start)
        self.end = int(end)

    def time_valid(self):
        return self.start > -1 and self.end > -1

    @property
    def speaker(self):
        return self._speaker
    @speaker.setter
    def speaker(self, value):
        DialogAct.speakers.add(value)
        self._speaker = value

class Annotation(QObject):
    visible_minutes_changed = Signal()
    num_colors_changed = Signal()
    modified_changed = Signal(bool)
    path_changed = Signal()

    def __init__(self, parent = None):
        super(Annotation, self).__init__(parent)
        self._modified = False
        self._transcript_file = None
        self._minutes_file = None
        self.selected_minutes = set()
        self.selected_das = set()
        self.minutes_files = []
        self.transcript_files = []
        self.minutes_index_map = dict()

        self._visible_minutes = set()

        self._das = []
        self._minutes = []

    def get_path(self):
        return self._path

    @property
    def modified(self):
        return self._modified
    @modified.setter
    def modified(self, value):
        self.modified_changed.emit(value)
        self._modified = value

    def get_minute(self, i) -> Minute:
        return self._minutes[i]

    def minutes_count(self):
        return len(self._minutes)

    def get_dialog_act(self, i) -> DialogAct:
        return self._das[i]

    def das_count(self):
        return len(self._das)

    def insert_da(self, i, da):
        self._das.insert(i, da)
        self.modified = True

    def remove_das(self, i, count):
        del self._das[i:i + count]
        self.modified = True

    def _make_minutes_index_map(self):
        self.minutes_index_map = dict([(m, idx) for idx, m in enumerate(self._minutes)])
        self.minutes_index_map[None] = None

    def insert_minute(self, i, da):
        self._minutes.insert(i, da)
        self._make_minutes_index_map()
        self.modified = True

    def remove_minutes(self, i, count):
        to_rm = set(self._minutes[i:i + count])
        for da in self._das:
            if da.minute in to_rm:
                da.minute = None
        del self._minutes[i:i + count]
        self._make_minutes_index_map()
        self.modified = True
    
    def set_path(self, p):
        self._prevent()
        self._path = p
        self.minutes_files = listdir(path.join(self._path, MINUTES_FOLDER))
        self.transcript_files = listdir(path.join(self._path, TRANSCRIPT_FOLDER))
        self.path_changed.emit()

    def _prevent(self):
        if self.modified:
            msg = QMessageBox()
            msg.setText('Save changes first!')
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.exec_()
            raise Exception('save changes first')

    def open_transcript(self, file):
        self._prevent()
        self._transcript_file = file
        full_path = path.join(self._path, TRANSCRIPT_FOLDER, file)
        data = []
        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line[:-1] #remove newline
                s = line.split(SEPARATOR)
                data.append(DialogAct(*s))
            self._das = data
        self.open_annotation()
        self.modified = False

    def open_minutes(self, file):
        self._prevent()
        self._minutes_file = file
        full_path = path.join(self._path, MINUTES_FOLDER, file)
        data = []
        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line[:-1] #remove newline
                data.append(Minute(line))
            self._minutes = data
            self._make_minutes_index_map()
        self.open_annotation()
        self.modified = False

    def open_annotation(self):
        for d in self._das:
            d.problem = None
            d.minute = None
        af = "{}+{}".format(
            self._transcript_file,
            self._minutes_file
        )
        self._annotation_file = af
        full_path = path.join(self._path, ANNOTATIONS_FOLDER, af)
        if path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    line = line.strip().split(' ')
                    idx = int(line[0])
                    d = self._das[idx]
                    minute = int(line[1]) if line[1].isdigit() else None
                    problem = int(line[2]) if line[2].isdigit() else None
                    d.problem = problem
                    try:
                        d.minute = self._minutes[minute]
                    except:
                        d.minute = None

    def _save_transcript(self):
        full_path = path.join(self._path, TRANSCRIPT_FOLDER, self._transcript_file)
        with open(full_path, 'w', encoding='utf-8') as f:
            for da in self._das:
                try:
                    f.write("".join([
                        da.text,
                        SEPARATOR,
                        da.speaker,
                        SEPARATOR,
                        str(da.start),
                        SEPARATOR,
                        str(da.end),
                        '\n'
                    ]))
                except:
                    pass

    def _save_minutes(self):
        full_path = path.join(self._path, MINUTES_FOLDER, self._minutes_file)
        with open(full_path, 'w', encoding='utf-8') as f:
            for m in self._minutes:
                f.write('{}\n'.format(m.text))

    def _save_annotation(self):
        af = "{}+{}".format(
            self._transcript_file,
            self._minutes_file
        )
        self._annotation_file = af
        full_path = path.join(self._path, ANNOTATIONS_FOLDER, af)
        with open(full_path, 'w', encoding='utf-8') as f:
            for idx, da in enumerate(self._das):
                if da.minute != None or da.problem != None:
                    midx = self.minutes_index_map[da.minute]
                    f.write('{} {} {}\n'.format(
                        idx,
                        midx,
                        da.problem
                    ))

    def save(self):
        self._save_annotation()
        self._save_minutes()
        self._save_transcript()
        self.modified = False

    def set_minute(self, minute = None):
        for da in self.selected_das:
            da.minute = minute
        self.modified = len(self.selected_das) > 0

    def set_problem(self, problem = None):
        for da in self.selected_das:
            da.problem = problem
        self.modified = len(self.selected_das) > 0

    @property
    def visible_minutes(self):
        return self._visible_minutes
    @visible_minutes.setter
    def visible_minutes(self, value):
        self._visible_minutes = set(value)
        self.visible_minutes_changed.emit()

    def get_minute_color(self, minute):
        OFFSET = 37
        i = self.minutes_index_map[minute]
        return QColor.fromHsv((OFFSET * i) % 360, 150, 250)

    def get_minute_text_color(self, minute):
        c = self.get_minute_color(minute)
        return QColor.fromHsv((c.hue() + 180) % 360, 0, 0)

    def is_minute_visible(self, minute):
        return minute in self.visible_minutes

    def expand_speakers(self):
        last_speaker = None
        for da in self._das:
            if da.speaker is None or len(da.speaker) == 0:
                da.speaker = last_speaker
            else:
                last_speaker = da.speaker
        self.modified = True