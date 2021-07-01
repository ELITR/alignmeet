import html

from PySide2 import QtCore
from PySide2.QtCore import Qt, QModelIndex, Slot

from ..problems import PROBLEMS
from ..annotation import Annotation

class DAModel(QtCore.QAbstractTableModel): 
    def __init__(self, annotation : Annotation, parent=None, *args): 
        super(DAModel, self).__init__()
        self.annotation = annotation
        self.annotation.modified_changed.connect(self.update)
        self.setHeaderData(0, Qt.Horizontal, "Speaker")
        self.setHeaderData(1, Qt.Horizontal, "Transcript")
        self.setHeaderData(2, Qt.Horizontal, "Problem")
        self.highlight = None
    
    @Slot()
    def update(self):
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.annotation.das_count()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 3

    def headerData(self, index, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if index == 0:
                    return 'Speaker'
                elif index == 1:
                    return 'Dialog Act'
                else:
                    return 'Problem'
            elif orientation == Qt.Vertical:
                if self.annotation.das_count() > index:
                    d = self.annotation.get_dialog_act(index)
                    if d.time_valid():
                        return '{:2d}:{:2.1f} - {:2d}:{:2.1f}'.format(
                            int(d.start // 60),
                            d.start - (d.start // 60) * 60,
                            int(d.end // 60),
                            d.end - (d.end // 60) * 60,
                        )
                return "{}".format(index + 1)
        else:
            return super().headerData(index, orientation, role=role)

    def setData(self, index, data, role=Qt.EditRole):
        if index.isValid():
            i = index.row()
            j = index.column()
            if role == Qt.EditRole and j < 2:
                d = self.annotation.get_dialog_act(i)
                val = None
                if j == 0:
                    val = d.speaker
                    d.speaker = data
                if j == 1:
                    val = d.text
                    d.text = data
                if val != data:
                    self.annotation.modified = True
                return True
        return False
        
    def insertRow(self, position, row, parent=QModelIndex()):
        self.beginInsertRows(QModelIndex(), position, position)

        self.annotation.insert_da(position, row)

        self.endInsertRows()
        return True

    def removeRows(self, pos, count, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), pos, pos + count - 1)

        self.annotation.remove_das(pos, count)

        self.endRemoveRows()
        return True

    def _highlight(self, text, role):
        text = html.escape(text)
        if self.highlight and role == Qt.DisplayRole:
            return self.highlight.sub('<b style="background-color: steelblue;">\g<0></b>', text)
        return text

    def data(self, index, role=Qt.DisplayRole):
        i = index.row()
        j = index.column()
        d = self.annotation.get_dialog_act(i)
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if j == 0:
                return self._highlight(d.speaker, role)
            if j == 1:
                return self._highlight(d.text, role)
            if j == 2:
                if d.problem is None:
                    return ""
                else:
                    return PROBLEMS[d.problem]
        elif role == Qt.BackgroundRole or role == Qt.ForegroundRole:
            if d.minute is None:
                return None
            else:
                if role == Qt.ForegroundRole:
                    return self.annotation.get_minute_text_color(d.minute)
                else:
                    return self.annotation.get_minute_color(d.minute)

    def flags(self, index):
        j = index.column()
        if j == 2:
            return super().flags(index)
        return  Qt.ItemIsEnabled | Qt.ItemIsEditable | super().flags(index)