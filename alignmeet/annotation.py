from os import path, listdir
import os
import re
import glob

from PySide2.QtCore import Signal, Slot, QObject
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QMessageBox, QUndoStack, QUndoView, QUndoCommand

SEPARATOR = '^'
TRANSCRIPT_FOLDER = 'transcripts'
MINUTES_FOLDER = 'minutes'
ANNOTATIONS_FOLDER = 'annotations'
EVALUATIONS_FOLDER = 'evaluations'

class Minute:
    # class for data of a single minute line
    max_id = -1
    def __init__(self, text = '', id = -1):
        super().__init__()
        if id == -1:
            id = Minute.max_id + 1
        self._id = id
        self.id = id
        self.text = text
        self.fluency = 1.0
        self.grammaticality = 1.0
        self.adequacy = 1.0
        self.relevance = 1.0

    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        Minute.max_id = max(value, Minute.max_id)
        self._id = value

class DialogAct:
    # class for data of a single transcript segment
    speakers = set()
    def __init__(self,  text = '', speaker = '',start = -1, end = -1, minute : Minute = None, problem = None):
        self._speaker = speaker
        if speaker is None or len(speaker) < 1:
            for f in re.findall('^\s*\([^)]+\)', text):
                speaker = f[1:-1]
                text = text.replace(f, '', 1)
                break
        self.speaker = speaker
        self.text = text
        self.minute = minute
        self.problem = problem
        self.start = float(start)
        self.end = float(end)

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
    #class that all widgets link to, stores data for the overall app
    visible_minutes_changed = Signal()
    num_colors_changed = Signal()
    modified_changed = Signal(bool)
    path_changed = Signal()
    undo_toggle = Signal(bool)
    redo_toggle = Signal(bool)

    def __init__(self, parent = None):
        super(Annotation, self).__init__(parent)
        self._path = ""
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
        self._document_level_adequacy = 1.0 #shows up at the bottom, how is it stored in the files?

        self.undo_stack = QUndoStack(self) # stores QUndoCommands (user actions) that can be undone/redone
        self.undo_view = QUndoView(self.undo_stack)

    def show_edit_history(self):
        self.undo_view.show()

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
        self.modified = False
        self._path = p
        self._refresh_files()
        self.path_changed.emit()

    def refresh(self):
        if os.path.exists(self._path):
            self._refresh_files()

    def _refresh_files(self):
        def clean_glob(files):
            return list(map(lambda f: f.split('/')[-1].split('\\')[-1], files))
        if os.path.exists(path.normpath(path.join(self._path, MINUTES_FOLDER))):
            self.minutes_files = listdir(path.normpath(path.join(self._path, MINUTES_FOLDER)))
        else:
            folder = path.normpath(path.join(self._path, 'minutes*.txt'))
            self.minutes_files = clean_glob(glob.glob(folder))

        if os.path.exists(path.normpath(path.join(self._path, TRANSCRIPT_FOLDER))):
            self.transcript_files = listdir(path.normpath(path.join(self._path, TRANSCRIPT_FOLDER)))
        else:
            folder = path.normpath(path.join(self._path, 'transcript*.txt'))
            self.transcript_files = clean_glob(glob.glob(folder))


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
        full_path = path.normpath(path.join(self._path, TRANSCRIPT_FOLDER, file))
        if not os.path.exists(full_path):
            full_path = path.normpath(path.join(self._path, file))
        data = []

        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                if line is None or len(line) < 1 or not any(map(lambda x: x.isalpha(), list(line))):
                    continue
                line = line[:-1] #remove newline
                s = line.split(SEPARATOR)
                data.append(DialogAct(*s))

        self._das = data
        self.open_annotation()
        self.open_evaluation()
        self.modified = False

    def open_minutes(self, file):
        self._prevent()
        self._minutes_file = file
        full_path = path.normpath(path.join(self._path, MINUTES_FOLDER, file))
        if not os.path.exists(full_path):
            full_path = path.normpath(path.join(self._path, file))
        data = []
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    line = line[:-1] #remove newline
                    data.append(Minute(line))
        except:
            pass
        self._minutes = data
        self._make_minutes_index_map()
        self.open_annotation()
        self.open_evaluation()
        self.modified = False

    def open_annotation(self):
        for d in self._das:
            d.problem = None
            d.minute = None
        annotations_path = path.normpath(path.join(self._path, ANNOTATIONS_FOLDER))
        annotations_prefix = '' if os.path.exists(annotations_path) else 'alignment+'
        af = "{}{}+{}".format(
            annotations_prefix,
            self._transcript_file,
            self._minutes_file
        )
        self._annotation_file = af
        full_path = path.join(self._path, ANNOTATIONS_FOLDER, af) if os.path.exists(annotations_path) else path.join(self._path, af)
        full_path = path.normpath(full_path)
        if path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    line = line.strip().split(' ')
                    idx = int(line[0]) - 1
                    d = self._das[idx]
                    minute = int(line[1]) - 1 if line[1].isdigit() else None
                    problem = int(line[2]) - 1 if line[2].isdigit() else None
                    d.problem = problem
                    try:
                        d.minute = self._minutes[minute]
                    except:
                        d.minute = None

    def open_evaluation(self):
        self._document_level_adequacy = 1.0
        evaluation_path = path.normpath(path.join(self._path, EVALUATIONS_FOLDER))
        evaluation_prefix = '' if os.path.exists(evaluation_path) else 'evaluation+'
        af = "{}{}+{}".format(
            evaluation_prefix,
            self._transcript_file,
            self._minutes_file
        )
        self._annotation_file = af
        full_path = path.join(self._path, EVALUATIONS_FOLDER, af) if os.path.exists(evaluation_path) else path.join(self._path, af)
        full_path = path.normpath(full_path)
        if path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self._document_level_adequacy = float(lines[0].strip())
                for m, e in zip(self._minutes, lines[1:]):
                    e = list(map(float, e.split(SEPARATOR)))
                    if all(map(lambda x: x > 0, e)):
                        m.adequacy = e[0]
                        m.grammaticality = e[1]
                        m.fluency = e[2]

    def _save_transcript(self):
        full_path = path.normpath(path.join(self._path, TRANSCRIPT_FOLDER, self._transcript_file))
        if not os.path.exists(full_path):
            full_path = path.normpath(path.join(self._path, self._transcript_file))
        with open(full_path, 'w', encoding='utf-8') as f:
            for da in self._das:
                try:
                    if da.speaker == '':
                        f.write("".join([
                            da.text,
                            '\n'
                        ]))
                    else:
                        f.write("".join([
                            '(',
                            da.speaker,
                            ')',
                            da.text,
                            '\n'
                        ]))
                except:
                    pass

    def _save_minutes(self):
        full_path = path.normpath(path.join(self._path, MINUTES_FOLDER, self._minutes_file))
        if not os.path.exists(full_path):
            full_path = path.normpath(path.join(self._path, self._minutes_file))
        with open(full_path, 'w', encoding='utf-8') as f:
            for m in self._minutes:
                f.write('{}\n'.format(m.text))

    def _save_annotation(self):
        annotations_path = path.normpath(path.join(self._path, ANNOTATIONS_FOLDER))
        annotations_prefix = '' if os.path.exists(annotations_path) else 'alignment+'
        af = "{}{}+{}".format(
            annotations_prefix,
            self._transcript_file,
            self._minutes_file
        )
        full_path = path.join(self._path, ANNOTATIONS_FOLDER, af) if os.path.exists(annotations_path) else path.join(self._path, af)
        full_path = path.normpath(full_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            for idx, da in enumerate(self._das):
                if da.minute != None or da.problem != None:
                    midx = self.minutes_index_map[da.minute]
                    f.write('{} {} {}\n'.format(
                        idx + 1,
                        midx + 1 if midx is not None else midx,
                        da.problem + 1 if da.problem is not None else da.problem
                    ))

    def _save_evaluation(self):
        evaluation_path = path.normpath(path.join(self._path, EVALUATIONS_FOLDER))
        evaluation_prefix = '' if os.path.exists(evaluation_path) else 'evaluation+'
        af = "{}{}+{}".format(
            evaluation_prefix,
            self._transcript_file,
            self._minutes_file
        )
        self._annotation_file = af
        full_path = path.join(self._path, EVALUATIONS_FOLDER, af) if os.path.exists(evaluation_path) else path.join(self._path, af)
        full_path = path.normpath(full_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f'{self._document_level_adequacy}\n')
            for m in self._minutes:
                if any([d.minute == m for d in self._das]):
                    f.write(f'{m.adequacy}{SEPARATOR}{m.grammaticality}{SEPARATOR}{m.fluency}\n')
                else:
                    f.write(f'{-1}{SEPARATOR}{-1}{SEPARATOR}{-1}\n')


    def save(self):
        self._save_annotation()
        self._save_evaluation()
        self._save_minutes()
        self._save_transcript()
        self.modified = False

    def set_minute(self, minute = None):
        if len(self.selected_das) > 0:
            command = AlignCommand(self, self.selected_das, minute, "Align transcript")
            self.push_to_undo_stack(command)
        else:
            print("no das selected, modified=false")
            self.modified = False

    def set_problem(self, problem = None):
        if len(self.selected_das) > 0:
            command = SetProblemCommand(self, self.selected_das, problem, f"Set problem {problem}")
            self.push_to_undo_stack(command)
        else:
            self.modified = False

    def push_to_undo_stack(self, command : QUndoCommand):
        self.undo_stack.push(command)

    @Slot()
    def undo(self):
        self.undo_stack.undo()

    @Slot()
    def redo(self):
        self.undo_stack.redo()

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


class AlignCommand(QUndoCommand):
    def __init__(self, annotation, transcript_rows : set, minute : Minute, text: str) -> None:
        super().__init__(text)
        self.annotation = annotation
        self.transcript_rows = transcript_rows
        self.new_minute = minute
        self.original_minutes = {tr : tr.minute for tr in transcript_rows}

    def redo(self):
        for row in self.transcript_rows:
            row.minute = self.new_minute
        
        self.annotation.modified = True

    def undo(self):
        for row in self.transcript_rows:
            row.minute = self.original_minutes[row]

        self.annotation.modified = True

class SetProblemCommand(QUndoCommand):
    def __init__(self, annotation, transcript_rows : set, problem : int, text: str) -> None:
        super().__init__(text)
        self.annotation = annotation
        self.transcript_rows = transcript_rows
        self.new_problem = problem
        self.original_problems = {tr : tr.problem for tr in transcript_rows}

    def redo(self):
        for row in self.transcript_rows:
            row.problem = self.new_problem
        
        self.annotation.modified = True

    def undo(self):
        for row in self.transcript_rows:
            row.problem = self.original_problems[row]

        self.annotation.modified = True