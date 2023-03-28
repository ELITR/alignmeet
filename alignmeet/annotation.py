from os import path, listdir
import os
import re
import glob

from PySide2.QtCore import Signal, Slot, QObject, QThread
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QMessageBox, QUndoStack, QUndoView, QUndoCommand
from .autoalign import Aligner, Embedder

SEPARATOR = '^'
TRANSCRIPT_FOLDER = 'transcripts'
MINUTES_FOLDER = 'minutes'
ANNOTATIONS_FOLDER = 'annotations'
EVALUATIONS_FOLDER = 'evaluations'

class MinuteEmbedThread(QThread):
        finished = Signal(list, str)
        def __init__(self, annotation, filename):
            super().__init__()
            self.annotation = annotation
            self.filename = filename
            
        def run(self):
            e = Embedder()
            embeds = e.embed(self.annotation._minutes)
            self.finished.emit(list(embeds), self.filename)
            
class TranscriptEmbedThread(QThread):
        finished = Signal(list, str)
        def __init__(self, annotation, filename):
            super().__init__()
            self.annotation = annotation
            self.filename = filename
            
        def run(self):
            e = Embedder()
            embeds = e.embed(self.annotation._das)
            self.finished.emit(list(embeds), self.filename)

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
        self.embed = None

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
    def __init__(self,  text = '', speaker = '',start = -1, end = -1, minute : Minute = None, problem = None, is_final = True):
        self._speaker = speaker
        if speaker is None or len(speaker) < 1:
            for f in re.findall('^\s*\([^)]+\)', text):
                speaker = f[1:-1]
                text = text.replace(f, '', 1)
                break
        self.speaker = speaker
        self.text = text
        self.minute = minute
        self.is_final = is_final
        self.problem = problem
        self.start = float(start)
        self.end = float(end)
        self.embed = None

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
    problems_changed = Signal()

    def __init__(self, annotations, undo = True, parent = None):
        super(Annotation, self).__init__(parent)
        
        self.annotations = annotations
        
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
        self._adequacy = 1.0
        self._grammaticality = 1.0
        self._fluency = 1.0
        self._relevance = 1.0
        
        self.tr_thread = None
        self.min_thread = None
        self.tr_embed_done = False
        self.min_embed_done = False
        
        
        self.threshold = 0.5 #for autoalign

        if undo:
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

    @Slot(list, str)
    def finalize_tr_embed(self, embeds, filename, save=True):
        if save:
            Embedder.saveEmbed(embeds, filename + '.embed')
        
        tr_ver = self.annotations.transcripts.transcript_ver
        # print(tr_ver.itemData(tr_ver.currentIndex()))
        # print(filename)
        # if filename == tr_ver.itemData(tr_ver.currentIndex()):
        for da, embed in zip(self._das, embeds):
            da.embed = embed
        self.tr_embed_done = True
        self.check_aa_action()
                
    @Slot(list, str)
    def finalize_min_embed(self, embeds, filename, save=True):
        if save:
            Embedder.saveEmbed(embeds, filename + '.embed')
        
        min_ver = self.annotations.minutes.minutes_ver
        # if filename == min_ver.itemData(min_ver.currentIndex()):
        for min, embed in zip(self._minutes, embeds):
            min.embed = embed
        self.min_embed_done = True
        self.check_aa_action()
        
    def check_aa_action(self):
        self.annotations.autoalignAction.setEnabled(self.tr_embed_done and self.min_embed_done)

    def open_transcript(self, file):
        self.tr_embed_done = False
        self.annotations.autoalignAction.setEnabled(False)
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
        
        if os.path.exists(full_path + '.embed'):
            embeds = Embedder.loadEmbed(full_path + '.embed')
            self.finalize_tr_embed(embeds, full_path, False)
        else:
            if self.tr_thread:
                self.tr_thread.terminate()
            self.tr_thread = TranscriptEmbedThread(self, full_path)
            self.tr_thread.finished.connect(self.finalize_tr_embed)
            self.tr_thread.start()
        
        self.open_annotation()
        self.open_evaluation()
        self.modified = False

    def open_minutes(self, file):
        self.min_embed_done = False
        self.annotations.autoalignAction.setEnabled(False)
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
        
        if os.path.exists(full_path + '.embed'):
            embeds = Embedder.loadEmbed(full_path + '.embed')
            self.finalize_min_embed(embeds, full_path, False)
        else:
            if self.min_thread:
                self.min_thread.terminate()
            self.min_thread = MinuteEmbedThread(self, full_path)
            self.min_thread.finished.connect(self.finalize_min_embed)
            self.min_thread.start()
        
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
                    
                    final = True
                    if line[1].isdigit():
                        minute = int(line[1]) - 1
                    elif str.endswith(line[1], '?') and line[1][:-1].isdigit():
                        minute = int(line[1][:-1]) - 1
                        final = False
                    else:
                        minute = None
                    
                    if line[2].isdigit():
                        num = int(line[2])-1
                        problem = int(line[2]) - 1 if num >= 0 else None
                    elif len(line[2]) >= 2 and line[2][:2] == '0:':
                        #custom problem
                        if len(line) > 3: # space in custom problem
                            problem = line[2][2:] + ' ' + ' '.join(line[3:])
                        else:
                            problem = line[2][2:]
                    else:
                        problem = None

                    d.problem = problem
                    d.is_final = final
                    try:
                        d.minute = self._minutes[minute]
                    except:
                        d.minute = None
            self.problems_changed.emit()

    def open_evaluation(self):
        self._adequacy = 1.0
        self._grammaticality = 1.0
        self._fluency = 1.0
        self._relevance = 1.0
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
                if SEPARATOR not in lines[0]:
                    self._adequacy = float(lines[0].strip())
                    self._grammaticality = 1.0
                    self._fluency = 1.0
                    self._relevance = 1.0
                else:
                    doclevel = list(map(float, lines[0].strip().split(SEPARATOR)))
                    self._adequacy = doclevel[0]
                    self._grammaticality = doclevel[1]
                    self._fluency = doclevel[2]
                    self._relevance = doclevel[3]
                
                for m, e in zip(self._minutes, lines[1:]):
                    e = list(map(float, e.split(SEPARATOR)))
                    if all(map(lambda x: x > 0, e)):
                        m.adequacy = e[0]
                        m.grammaticality = e[1]
                        m.fluency = e[2]
                        m.relevance = e[3] if len(e) > 3 else 1.0

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
                    if isinstance(da.problem, str):
                        problem = f'0:{da.problem}'
                    elif da.problem:
                        problem = da.problem + 1
                    else:
                        problem = None
                    f.write('{} {}{} {}\n'.format(
                        idx + 1,
                        midx + 1 if midx is not None else midx,
                        '?' if not da.is_final else '',
                        problem
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
            f.write(f'{self._adequacy}{SEPARATOR}{self._grammaticality}{SEPARATOR}{self._fluency}{SEPARATOR}{self._relevance}\n')
            for m in self._minutes:
                if any([d.minute == m for d in self._das]):
                    f.write(f'{m.adequacy}{SEPARATOR}{m.grammaticality}{SEPARATOR}{m.fluency}{SEPARATOR}{m.relevance}\n')
                else:
                    f.write(f'{-1}{SEPARATOR}{-1}{SEPARATOR}{-1}\n')


    def save(self):
        self._save_annotation()
        self._save_evaluation()
        self._save_minutes()
        self._save_transcript()
        self.modified = False

    def set_minute(self, minute = None):
        same = True
        for d in self.selected_das:
            if not d.minute == minute:
                same = False
                break
            if not d.is_final:
                same = False
                break
                
        if len(self.selected_das) > 0 and not same:
            command = AlignCommand(self, self.selected_das, minute, "Align transcript")
            self.push_to_undo_stack(command)
        else:
            print("no das selected, modified=false")
            self.modified = False

    @Slot(object)
    def set_problem(self, problem = None):
        same = True
        for d in self.selected_das:
            if not d.problem == problem:
                same = False
                
        if len(self.selected_das) > 0 and not same:
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
        
    def finalize(self):
        final = True
        for da in self.selected_das:
            if not da.is_final:
                final = False
                break
            
        if len(self.selected_das) > 0 and not final:
            command = FinalizeCommand(self, self.selected_das, f"Finalize partial")
            self.push_to_undo_stack(command)
            
    def finalizeAll(self):
        final = True
        for da in self._das:
            if da.is_final:
                final = False
                break
            
        if len(self._das) > 0 and not final:
            command = FinalizeCommand(self, self._das, f"Finalize all")
            self.push_to_undo_stack(command)
            
        
class FinalizeCommand(QUndoCommand):
    def __init__(self, annotation, transcript_rows : set, text: str) -> None:
        super().__init__(text)
        self.annotation = annotation
        self.transcript_rows = transcript_rows
        self.original_final = {tr : tr.is_final for tr in transcript_rows}
        
    def redo(self):
        for row in self.transcript_rows:
            if row.minute:
                row.is_final = True
        
        self.annotation.modified = True

    def undo(self):
        for row in self.transcript_rows:
            row.is_final = self.original_final[row]

        self.annotation.modified = True

class AlignCommand(QUndoCommand):
    def __init__(self, annotation, transcript_rows : set, minute : Minute, text: str) -> None:
        super().__init__(text)
        self.annotation = annotation
        self.transcript_rows = transcript_rows
        self.new_minute = minute
        self.original_minutes = {tr : tr.minute for tr in transcript_rows}
        self.original_final = {tr : tr.is_final for tr in transcript_rows}
        
    def redo(self):
        for row in self.transcript_rows:
            row.minute = self.new_minute
            row.is_final = True
        
        self.annotation.modified = True

    def undo(self):
        for row in self.transcript_rows:
            row.minute = self.original_minutes[row]
            row.is_final = self.original_final[row]

        self.annotation.modified = True

class SetProblemCommand(QUndoCommand):
    def __init__(self, annotation, transcript_rows : set, problem, text: str) -> None:
        super().__init__(text)
        self.annotation = annotation
        self.transcript_rows = transcript_rows
        self.new_problem = problem
        self.original_problems = {tr : tr.problem for tr in transcript_rows}

    def redo(self):
        for row in self.transcript_rows:
            row.problem = self.new_problem
        
        self.annotation.problems_changed.emit()
        self.annotation.modified = True

    def undo(self):
        for row in self.transcript_rows:
            row.problem = self.original_problems[row]

        self.annotation.problems_changed.emit()
        self.annotation.modified = True