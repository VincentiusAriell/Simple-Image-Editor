import cv2
from PyQt5 import QtCore
from process.effects import apply_effects_cv2

class WorkerSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(object)

class ApplyWorker(QtCore.QRunnable):
    def __init__(self, cv2_img, params):
        super().__init__()
        self.signals = WorkerSignals()
        # copy image to avoid mutation
        self.cv2_img = cv2_img.copy() if cv2_img is not None else None
        self.params = params or {}

    @QtCore.pyqtSlot()
    def run(self):
        if self.cv2_img is None:
            self.signals.result.emit(None)
            return
        try:
            res = apply_effects_cv2(self.cv2_img, **self.params)
            self.signals.result.emit(res)
        except Exception as e:
            print('apply worker error', e)
            self.signals.result.emit(self.cv2_img)
