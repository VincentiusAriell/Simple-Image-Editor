import os
from PyQt5 import QtWidgets

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def get_filename(path: str):
    return os.path.splitext(os.path.basename(path))[0]


def get_extension(path: str):
    return os.path.splitext(path)[1].lower()


def generate_save_path(original_path: str, suffix: str = "_edited"):
    folder = os.path.dirname(original_path)
    name = get_filename(original_path)
    ext = get_extension(original_path)
    return os.path.join(folder, f"{name}{suffix}{ext}")


def ask_save_path(parent, default_name="edited_image.jpg"):
    dialog = QtWidgets.QFileDialog(parent)
    dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
    dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
    dialog.setDefaultSuffix("jpg")

    path, ok = dialog.getSaveFileName(
        parent,
        "Save Image",
        default_name,
        "Images (*.jpg *.jpeg *.png *.bmp)"
    )

    return path if ok else None
