from copy import copy
from typing import KeysView

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
        self.owner = owner

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
            if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                if event.modifiers() == QtCore.Qt.ControlModifier:
                    if self.editor is not None:
                        pos = self.editor.textCursor().position()
                        self.textToSplit = pos
                self.editor.clearFocus()
                return True
            elif event.key() == QtCore.Qt.Key_Escape:
                if self.editor.toPlainText() == '' and self.last_val == '':
                    self.remove_row.emit()
                self.editor.clearFocus()
        return super().eventFilter(source, event)

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.EditRole)
        self.last_val = value
        editor.setText(value)

    def setModelData(self, editor, model, index):
        value = editor.toPlainText()
        self.editor = None
        if (not model.data(index) == value or not self.textToSplit == None): #if changed
            command = EditTextCommand(value, self.textToSplit, model, index)
            self.textToSplit = None
            self.owner.annotation.push_to_undo_stack(command)
        
        self.end_editing.emit()

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def anchorAt(self, html, point):
        doc = QtGui.QTextDocument()
        doc.setHtml(html)
        textLayout = doc.documentLayout()
        return textLayout.anchorAt(point)

    def paint(self, painter, option, index):
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        if options.widget:
            style = options.widget.style()
        else:
            style = QtWidgets.QApplication.style()

        doc = QtGui.QTextDocument()
        option = QtGui.QTextOption(doc.defaultTextOption())
        option.setWrapMode(QtGui.QTextOption.WordWrap)
        doc.setDefaultTextOption(option)
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        options.text = ''

        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter)
        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, options)

        painter.save()

        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        painter.translate(0, 0.5*(options.rect.height() - doc.size().height()))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QtGui.QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())

        return QtCore.QSize(doc.idealWidth(), doc.size().height())

class EditTextCommand(QtWidgets.QUndoCommand):
    def __init__(self, value, textToSplit, model, index):
        super().__init__("Text edit") #TODO: put beginning of text
        self.value = value
        self.textToSplit = textToSplit
        self.model = model
        self.index = index
    
    def redo(self):
        self.old_data = self.model.data(self.index)
        self.model.setData(self.index, self.value[:self.textToSplit], QtCore.Qt.EditRole)
        if self.textToSplit is not None:
            row = copy(self.model.annotation.get_dialog_act(self.index.row()))
            row.text = self.value[self.textToSplit:]
            self.model.insertRow(self.index.row() + 1, row)

    def undo(self):
        self.model.setData(self.index, self.old_data, QtCore.Qt.EditRole)
        if self.textToSplit is not None:
            self.model.removeRows(self.index.row()+1, 1)