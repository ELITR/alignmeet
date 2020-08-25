import os
import io

from PySide2 import QtCore
from PySide2.QtCore import Qt, QModelIndex, Signal, Slot
from PySide2.QtGui import QBrush
from PySide2.QtWidgets import QMessageBox

from problems import PROBLEMS
from annotation import Minute

class MinutesModel(QtCore.QAbstractTableModel): 

    def __init__(self, annotation, parent=None, *args): 
        super(MinutesModel, self).__init__()
        self.annotation = annotation
        self.annotation.modified_changed.connect(self.update)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Minute")
        self.annotation.visible_minutes_changed.connect(self.update)

    @Slot()
    def update(self):
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.annotation.minutes_count() 

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def headerData(self, index, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if index == 0:
                    return 'Minute'
        return super().headerData(index, orientation, role=role)

    def setData(self, index, data, role=Qt.EditRole):
        if index.isValid():
            i = index.row()
            if role == Qt.EditRole:
                self.annotation.get_minute(i).text = data
                return True
        return False
        
    def insertRow(self, position, row, parent=QModelIndex()):
        self.beginInsertRows(QModelIndex(), position, position)
        self.annotation.insert_minute(position, row)

        self.endInsertRows()
        return True

    def removeRows(self, pos, count, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), pos, pos + count - 1)

        self.annotation.remove_minutes(pos, count)

        self.endRemoveRows()
        return True

    def data(self, index, role=QtCore.Qt.DisplayRole):
        i = index.row()
        j = index.column()
        m = self.annotation.get_minute(i)
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return m.text
        elif role == Qt.BackgroundRole:
            if self.annotation.is_minute_visible(m):
                return self.annotation.get_minute_color(m)
        elif role == Qt.ForegroundRole:
            if self.annotation.is_minute_visible(m):                
                return self.annotation.get_minute_text_color(m)
        else:
            return None

    def flags(self, index):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | super().flags(index)
