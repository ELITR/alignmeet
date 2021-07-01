from PySide2 import QtCore
from PySide2.QtCore import Qt, QModelIndex, Slot

class MinutesModel(QtCore.QAbstractTableModel): 

    def __init__(self, annotation, parent=None, *args): 
        super(MinutesModel, self).__init__()
        self.annotation = annotation
        self.annotation.modified_changed.connect(self.update)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Summary")
        self.annotation.visible_minutes_changed.connect(self.update)
        self._evaluation_mode = False

    def set_evaluation_mode(self, evaluation):
        self._evaluation_mode = evaluation
        self.update() #redraws

    @Slot()
    def update(self):
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.annotation.minutes_count() 

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4 if self._evaluation_mode else 1

    def headerData(self, index, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if index == 0:
                    return 'Summary'
                if index == 1:
                    return 'Adequacy'
                if index == 2:
                    return 'Grammaticality'
                if index == 3:
                    return 'Fluency'
        return super().headerData(index, orientation, role=role)

    def setData(self, index, data, role=Qt.EditRole):
        if index.isValid():
            i = index.row()
            j = index.column()
            if role == Qt.EditRole:
                m = self.annotation.get_minute(i)
                val = None
                if j == 0:
                    val = m.text
                    m.text = data

                else:
                    if data < 1:
                        data = 1
                    if data > 5:
                        data = 5
                    if j == 1:
                        val = m.adequacy
                        m.adequacy = data
                    if j == 2:
                        val = m.grammaticality
                        m.grammaticality = data
                    if j == 3:
                        val = m.fluency
                        m.fluency = data
                if val != data:
                    self.annotation.modified = True
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
            if j == 0:
                return m.text
            if any([d.minute == m for d in self.annotation._das]):
                if j == 1:
                    return m.adequacy
                if j == 2:
                    return m.grammaticality
                if j == 3:
                    return m.fluency
        elif role == Qt.BackgroundRole:
            if self.annotation.is_minute_visible(m):
                return self.annotation.get_minute_color(m)
        elif role == Qt.ForegroundRole:
            if self.annotation.is_minute_visible(m):                
                return self.annotation.get_minute_text_color(m)
        else:
            return None

    def flags(self, index):
        i = index.row()
        j = index.column()
        if self._evaluation_mode:
            m = self.annotation.get_minute(i)
            if self.annotation.is_minute_visible(m) and j > 0:
                return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | super().flags(index)
            else:
                return  Qt.NoItemFlags
        else:
            return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | super().flags(index)
            