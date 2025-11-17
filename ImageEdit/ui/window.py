import cv2
from PyQt5 import QtWidgets, QtCore, QtGui
from ui.controls import ControlPanel
from ui.crop_widget import CropLabel
from process.editor import Editor
from process.workers import ApplyWorker
from utils.converters import cv2_to_qpixmap, scaled_size_for_label
from process.histogram import histogram_image_from_cv2

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Editor - Modular")
        self.resize(1200, 760)

        
        self.editor = Editor()

        # UI elements
        top_buttons = QtWidgets.QHBoxLayout()
        self.open_btn = QtWidgets.QPushButton("Open Image")
        self.save_btn = QtWidgets.QPushButton("Save Edited")
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.undo_btn = QtWidgets.QPushButton("Undo")
        self.redo_btn = QtWidgets.QPushButton("Redo")
        self.rotate_left_btn = QtWidgets.QPushButton("⟲")
        self.rotate_right_btn = QtWidgets.QPushButton("⟳")

        top_buttons.addWidget(self.open_btn)
        top_buttons.addWidget(self.save_btn)
        top_buttons.addWidget(self.reset_btn)
        top_buttons.addWidget(self.undo_btn)
        top_buttons.addWidget(self.redo_btn)
        top_buttons.addWidget(self.rotate_left_btn)
        top_buttons.addWidget(self.rotate_right_btn)
        top_buttons.addStretch()

        self.open_btn.clicked.connect(self.open_image)
        self.save_btn.clicked.connect(self.save_image)
        self.reset_btn.clicked.connect(self.reset)
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn.clicked.connect(self.redo)
        self.rotate_left_btn.clicked.connect(lambda: self.rotate(-90))
        self.rotate_right_btn.clicked.connect(lambda: self.rotate(90))

        # Before / After
        self.before_label = QtWidgets.QLabel("Before")
        self.before_view = QtWidgets.QLabel()
        self.before_view.setAlignment(QtCore.Qt.AlignCenter)
        self.before_view.setMinimumSize(360, 300)
        self.before_view.setStyleSheet("background:#111;")

        self.after_label = QtWidgets.QLabel("After (drag to crop)")
        self.after_view = CropLabel()
        self.after_view.setAlignment(QtCore.Qt.AlignCenter)
        self.after_view.setMinimumSize(360, 300)
        self.after_view.setStyleSheet("background:#111;")

        self.after_view.mouse_pressed.connect(self.on_crop_press)
        self.after_view.mouse_moved.connect(self.on_crop_move)
        self.after_view.mouse_released.connect(self.on_crop_release)

        images_layout = QtWidgets.QHBoxLayout()
        left_v = QtWidgets.QVBoxLayout()
        left_v.addWidget(self.before_label)
        left_v.addWidget(self.before_view)
        right_v = QtWidgets.QVBoxLayout()
        right_v.addWidget(self.after_label)
        right_v.addWidget(self.after_view)

        # Histogram
        hist_v = QtWidgets.QVBoxLayout()
        hist_label = QtWidgets.QLabel("Histogram (RGB)")
        hist_label.setAlignment(QtCore.Qt.AlignCenter)
        self.hist_view = QtWidgets.QLabel()
        self.hist_view.setMinimumHeight(120)
        hist_v.addWidget(hist_label)
        hist_v.addWidget(self.hist_view)

        images_layout.addLayout(left_v)
        images_layout.addLayout(right_v)
        images_layout.addLayout(hist_v)

        # Controls panel
        self.controls = ControlPanel(self.apply_params_changed)

        # main layout
        main_v = QtWidgets.QVBoxLayout(self)
        main_v.addLayout(top_buttons)
        main_v.addLayout(images_layout)
        main_v.addWidget(self.controls)

        # thread pool for background processing
        self.threadpool = QtCore.QThreadPool()

        # crop state
        self._crop_start = None
        self._crop_end = None
        self._cropping = False

    def open_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if not path:
            return
        self.editor.load_image(path)
        self.update_views()
        self.editor.push_history()

    def save_image(self):
        if self.editor.edited is None:
            QtWidgets.QMessageBox.information(self, "No image", "Load and edit an image first")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save edited image", "", "PNG (*.png);;JPEG (*.jpg *.jpeg)")
        if not path:
            return
        ok = self.editor.save_image(path)
        if ok:
            QtWidgets.QMessageBox.information(self, "Saved", "Image saved")

    def reset(self):
        self.editor.reset_to_original()
        self.update_views()
        self.editor.push_history()

    def undo(self):
        self.editor.undo()
        self.update_views()

    def redo(self):
        self.editor.redo()
        self.update_views()

    def rotate(self, angle):
        self.editor.rotate(angle)
        self.update_views()
        self.editor.push_history()

    def apply_params_changed(self, params):
        # spawn worker
        worker = ApplyWorker(self.editor.original, params)
        worker.signals.result.connect(self.on_worker_result)
        self.threadpool.start(worker)

    def on_worker_result(self, pil_img):
        self.editor.edited = pil_img
        self.update_views()
        # push into history after user stops changing (ControlPanel does debouncing and will call push_history_when_set)

    def update_views(self):
        # update before and after pixmaps and histogram
        if self.editor.original is not None:
            scaled = cv2.resize(self.editor.original, scaled_size_for_label(self.before_view))
            pix = cv2_to_qpixmap(scaled)
            self.before_view.setPixmap(pix)
        if self.editor.edited is not None:
            scaled = cv2.resize(self.editor.edited, scaled_size_for_label(self.after_view))
            pix = cv2_to_qpixmap(scaled)
            # if cropping draw overlay handled by CropLabel
            self.after_view.setPixmap(pix)
            hist = histogram_image_from_cv2(self.editor.edited, width=512, height=120)
            self.hist_view.setPixmap(cv2_to_qpixmap(hist))

    # --- crop handlers ---
    def on_crop_press(self, e):
        if self.editor.edited is None:
            return
        self._cropping = True
        self._crop_start = (e.x(), e.y())
        self._crop_end = (e.x(), e.y())

    def on_crop_move(self, e):
        if not self._cropping:
            return
        self._crop_end = (e.x(), e.y())
        # request crop rectangle painting
        self.after_view.setCropRect(self._crop_start, self._crop_end)

    def on_crop_release(self, e):
        if not self._cropping:
            return
        self._crop_end = (e.x(), e.y())
        self._cropping = False
        self.after_view.clearCropRect()
        # compute image coords and crop
        disp_w = self.after_view.width()
        disp_h = self.after_view.height()
        img_h, img_w = self.editor.edited.shape[:2]
        sx = img_w / disp_w
        sy = img_h / disp_h
        x1 = int(min(self._crop_start[0], self._crop_end[0]) * sx)
        y1 = int(min(self._crop_start[1], self._crop_end[1]) * sy)
        x2 = int(max(self._crop_start[0], self._crop_end[0]) * sx)
        y2 = int(max(self._crop_start[1], self._crop_end[1]) * sy)
        if x2-x1 > 5 and y2-y1 > 5:
            self.editor.crop((x1, y1, x2, y2))
            self.update_views()
            self.editor.push_history()
