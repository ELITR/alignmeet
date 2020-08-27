from copy import copy

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Signal

class DialogActEditor(QtWidgets.QStyledItemDelegate):
    end_editing = Signal()
    remove_row = Signal()


    def __init__(self, owner):
        super().__init__(owner)
        self.editor = None
        self.textToSplit = None
        self.last_val = None

    def paint(self, painter, option, index):
        if isinstance(self.parent(), QtWidgets.QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super(DialogActEditor, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QTextEdit(parent)
        editor.setWordWrapMode(QtGui.QTextOption.WordWrap)
        editor.setAcceptRichText(False)
        self.editor = editor
        return editor

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier:
                if self.editor is not None:
                    pos = self.editor.cursorPosition()
                    self.textToSplit = pos
            if event.key() == QtCore.Qt.Key_Escape:
                if self.editor.toPlainText() == '' and self.last_val == '':
                    self.remove_row.emit()
        return super().eventFilter(source, event)

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        self.last_val = value
        editor.setText(value)

    def setModelData(self, editor, model, index):
        value = editor.toPlainText()
        self.editor = None
        model.setData(index, value[:self.textToSplit], QtCore.Qt.EditRole)
        if self.textToSplit is not None:
            row = copy(model.annotation.get_dialog_act(index.row()))
            row.text = value[self.textToSplit:]
            model.insertRow(index.row() + 1, row)
            self.textToSplit = None
        self.end_editing.emit()

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)