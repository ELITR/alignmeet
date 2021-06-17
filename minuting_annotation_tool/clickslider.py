from PySide2.QtWidgets import QSlider
from PySide2.QtCore import Signal

class ClickSlider(QSlider):
    mouse_pressed = Signal()
    mouse_released = Signal()

    def __init__(self, QtOrientation, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, QMouseEvent):
        self.mouse_pressed.emit()
        return super().mousePressEvent(QMouseEvent)

    def mouseReleaseEvent(self, QMouseEvent):
        self.mouse_released.emit()
        return super().mouseReleaseEvent(QMouseEvent)