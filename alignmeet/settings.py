import os

from PySide2.QtWidgets import QDialog, QFormLayout, QComboBox, QLineEdit, QSpinBox, QApplication
from PySide2.QtCore import Slot, Qt, QSettings
from PySide2.QtGui import QFontDatabase, QFont, QPalette, QColor


class Settings(QDialog):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.settings = QSettings(self)

        self.setWindowTitle('Annotations - settings')
        f = QFormLayout()
        self.setLayout(f)

        c = self.setup_combo(['Light', 'Dark'], 'theme')
        self.theme = c
        c.currentIndexChanged.connect(self._theme_changed)
        f.addRow('Theme', c)

        c = self.setup_combo(QFontDatabase().families(), 'family')
        self.family = c
        c.currentIndexChanged.connect(self._font_changed)
        f.addRow('Font', c)

        c = QSpinBox(self)
        c.setValue(int(self.settings.value('size')))
        self.size = c
        c.setMaximum(30)
        c.setMinimum(5)
        c.valueChanged.connect(self._font_changed)
        f.addRow('Font size', c)

        c = QLineEdit(self)
        c.setText(self.settings.value('annotator', ""))
        self.token = c
        c.textChanged.connect(lambda text: self.settings.setValue('annotator', text))
        f.addRow('Annotator name', c)

        c = QLineEdit(self)
        c.setText(self.settings.value('repo_location', os.path.abspath('./repository')))
        self.token = c
        c.textChanged.connect(lambda text: self.settings.setValue('repo_location', text))
        f.addRow('Repo location', c)

        c = QLineEdit(self)
        c.setText(self.settings.value('repository'))
        self.token = c
        c.textChanged.connect(lambda text: self.settings.setValue('repository', text))
        f.addRow('Repository', c)

        c = QLineEdit(self)
        c.setText(self.settings.value('user'))
        self.token = c
        c.textChanged.connect(lambda text: self.settings.setValue('user', text))
        f.addRow('Repo user', c)

        c = QLineEdit(self)
        c.setText(self.settings.value('token'))
        self.token = c
        c.textChanged.connect(lambda text: self.settings.setValue('token', text))
        f.addRow('Repo token', c)

        c = QLineEdit(self)
        c.textChanged.connect(lambda text: self.settings.setValue('indent', text))
        c.setText(self.settings.value('indent', defaultValue='-'))
        self.token = c
        f.addRow('Summary indent', c)

    def setup_combo(self, values, name):
        c = QComboBox(self)
        c.addItems(values)
        val = self.settings.value(name)
        try:
            idx = values.index(val)        
            c.setCurrentIndex(idx)
        except:
            pass
        return c

    @Slot()
    def _theme_changed(self):
        self.settings.setValue('theme', self.theme.currentText())
        Settings.apply_settings()

    @Slot()
    def _font_changed(self):
        f = self.family.currentText()
        s = self.size.value()
        self.settings.setValue('family', f)
        self.settings.setValue('size', s)
        f = QFont(f, s, QFont.PreferAntialias)
        f.setStyleStrategy(QFont.PreferQuality)
        QApplication.setFont(f)

    @staticmethod
    def get_value(name, default, settings=None):
        if settings is None:
            settings = QSettings()
        v = settings.value(name)
        if v is None:
            settings.setValue(name, default)
            v = default
        if isinstance(default, int):
            return int(v)
        return v


    @staticmethod
    def apply_settings():
        f = Settings.get_value('family', 'Serif')
        size = Settings.get_value('size', 11)

        f = QFont(f, size, QFont.PreferAntialias)
        f.setStyleStrategy(QFont.PreferQuality)

        theme = Settings.get_value('theme', 'Light')
        if theme == 'Light':
            p = QPalette()
            QApplication.setPalette(p)
        else:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            QApplication.setPalette(palette)