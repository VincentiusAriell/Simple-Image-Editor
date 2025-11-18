from PyQt5 import QtWidgets, QtCore, QtGui

class CropLabel(QtWidgets.QLabel):
    mouse_pressed = QtCore.pyqtSignal(object)
    mouse_moved = QtCore.pyqtSignal(object)
    mouse_released = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._crop_rect = None

    def mousePressEvent(self, e):
        self.mouse_pressed.emit(e)

    def mouseMoveEvent(self, e):
        self.mouse_moved.emit(e)

    def mouseReleaseEvent(self, e):
        self.mouse_released.emit(e)

    def setCropRect(self, start, end):
        self._crop_rect = (start, end)
        self.update()

    def clearCropRect(self):
        self._crop_rect = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._crop_rect is None:
            return
        start, end = self._crop_rect
        x1, y1 = start
        x2, y2 = end
        rect = QtCore.QRect(min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1))
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(QtGui.QColor(255, 255, 0, 200), 2)
        painter.setPen(pen)
        painter.drawRect(rect)
        painter.end()
