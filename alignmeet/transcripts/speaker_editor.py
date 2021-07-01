from PySide2 import QtCore, QtGui, QtWidgets

from ..annotation import DialogAct

class SpeakerEditor(QtWidgets.QStyledItemDelegate):

    def __init__(self, owner):
        super().__init__(owner)

    def paint(self, painter, option, index):
        if isinstance(self.parent(), QtWidgets.QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super(SpeakerEditor, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QComboBox(parent)
        editor.currentIndexChanged.connect(self.commit_editor)
        editor.addItems(DialogAct.speakers)
        editor.setEditable(True)
        return editor

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        num = list(DialogAct.speakers).index(value)
        editor.setCurrentIndex(num)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)

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
        doc.setHtml(options.text)
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