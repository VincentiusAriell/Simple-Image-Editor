import cv2
from process.effects import apply_effects
import os

class Editor:
    def __init__(self):
        self.original = None
        self.edited = None
        self.effects = []
        self.history = []
        self.future = []

    def load_image(self, file_path):
        self.original = cv2.imread(file_path)
        if self.original is not None:
            self.edited = self.original.copy()
            self.history = [self.edited.copy()]
            self.future = []

    def save_image(self, file_path):
        if self.edited is not None:
            cv2.imwrite(file_path, self.edited)
            return True
        return False

    def apply_effects(self):
        if self.original is not None:
            self.edited = apply_effects(self.original, self.effects)
            self.history.append(self.edited.copy())
            self.future = []

    def add_effect(self, effect):
        self.effects.append(effect)
        self.apply_effects()

    def undo(self):
        if len(self.history) > 1:
            self.future.append(self.history.pop())
            self.edited = self.history[-1].copy()

    def redo(self):
        if self.future:
            self.history.append(self.future.pop())
            self.edited = self.history[-1].copy()

    def rotate(self, angle):
        if self.edited is not None:
            h, w = self.edited.shape[:2]
            center = (w / 2, h / 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            self.edited = cv2.warpAffine(self.edited, M, (w, h))

    def crop(self, box):
        if self.edited is not None:
            x1, y1, x2, y2 = box
            self.edited = self.edited[y1:y2, x1:x2]

    def apply_params(self, params):
        if self.original is None:
            return
        self.edited = apply_effects(self.original, params)

    def reset_to_original(self):
        if self.original is not None:
            self.edited = self.original.copy()
            self.history = [self.edited.copy()]
            self.future = []

    def push_history(self):
        if self.edited is not None:
            self.history.append(self.edited.copy())
            self.future = []
