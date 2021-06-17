from PySide2 import QtCore, QtWidgets

class MinutesEditor(QtWidgets.QStyledItemDelegate):
    def __init__(self, owner):
        super().__init__(owner)

    def paint(self, painter, option, index):
        if isinstance(self.parent(), QtWidgets.QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super(MinutesEditor, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QPlainTextEdit(parent)
        self.editor = editor
        return editor

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        editor.setPlainText(value)

    def setModelData(self, editor, model, index):
        value = editor.toPlainText()
        self.editor = None
        model.setData(index, value, QtCore.Qt.EditRole)
        #self.end_editing.emit()

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)