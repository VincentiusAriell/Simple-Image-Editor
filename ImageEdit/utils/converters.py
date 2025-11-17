import cv2
from PyQt5 import QtGui, QtCore


def cv2_to_qpixmap(im) -> QtGui.QPixmap:
    # im is numpy array in BGR
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGBA)
    h, w, c = im.shape
    data = im.tobytes()
    qimage = QtGui.QImage(data, w, h, QtGui.QImage.Format_RGBA8888)
    return QtGui.QPixmap.fromImage(qimage)


def scaled_size_for_label(label):
    w = max(200, label.width() if label.width() > 0 else 360)
    h = max(150, label.height() if label.height() > 0 else 300)
    return (w, h)
