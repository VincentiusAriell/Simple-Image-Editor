from PyQt5 import QtWidgets, QtCore
import functools


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        layout = QtWidgets.QGridLayout(self)

        self.sliders = {}  # can contain QSlider, QCheckBox, QComboBox
        self.labels = {}

        # Format: (Nama Label, Min Value, Max Value, Default Value)
        names = [
            ("Brightness", -100, 100, 0),
            ("Contrast", -99, 99, 0),
            ("Highlights", -100, 100, 0),
            ("Shadows", -100, 100, 0),
            ("Saturation", -100, 100, 0),
            ("Tint", -100, 100, 0),
            ("Temperature", -100, 100, 0),
            ("Sharpness", -100, 100, 0),
            # --- NEW CONTROLS ---
            ("Denoise", 0, 9, 0),   # Median Blur strength
            # Invert and Edge will be implemented as checkbox (on/off)
            # Edge has an additional combo box to select method
        ]

        row = 0
        for name, mn, mx, init in names:
            lbl = QtWidgets.QLabel(f"{name}: {init}")
            s = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            s.setMinimum(int(mn))
            s.setMaximum(int(mx))
            s.setValue(int(init))
            s.valueChanged.connect(functools.partial(self.on_change, name, lbl))

            layout.addWidget(lbl, row, 0)
            layout.addWidget(s, row, 1)

            self.sliders[name] = s
            self.labels[name] = lbl
            row += 1

        # Invert: replace slider with checkbox
        inv_lbl = QtWidgets.QLabel("Invert: Off")
        inv_chk = QtWidgets.QCheckBox()
        inv_chk.stateChanged.connect(lambda v, n='Invert', l=inv_lbl: self.on_checkbox_change(n, l, v))
        layout.addWidget(inv_lbl, row, 0)
        layout.addWidget(inv_chk, row, 1)
        self.sliders['Invert'] = inv_chk
        self.labels['Invert'] = inv_lbl
        row += 1

        # Edge: checkbox + combobox for method
        edge_lbl = QtWidgets.QLabel("Edge: Off (Canny)")
        edge_chk = QtWidgets.QCheckBox()
        edge_chk.stateChanged.connect(lambda v, n='Edge', l=edge_lbl: self.on_checkbox_change(n, l, v))
        edge_combo = QtWidgets.QComboBox()
        edge_combo.addItems(["Canny", "Sobel"])
        edge_combo.currentIndexChanged.connect(lambda i, n='Edge', l=edge_lbl: self.on_edge_mode_change(n, l))

        # Put checkbox and combo in a horizontal widget
        edge_widget = QtWidgets.QWidget()
        edge_h = QtWidgets.QHBoxLayout(edge_widget)
        edge_h.setContentsMargins(0, 0, 0, 0)
        edge_h.addWidget(edge_chk)
        edge_h.addWidget(edge_combo)

        layout.addWidget(edge_lbl, row, 0)
        layout.addWidget(edge_widget, row, 1)
        self.sliders['Edge'] = (edge_chk, edge_combo)
        self.labels['Edge'] = edge_lbl
        row += 1

        # debounce timer
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.fire_callback)

    def on_change(self, name, label, value):
        label.setText(f"{name}: {value}")
        self.timer.start()

    def on_checkbox_change(self, name, label, state):
        text = 'On' if state else 'Off'
        # For edge, show selected method too
        if name == 'Edge':
            chk, combo = self.sliders['Edge']
            mode = combo.currentText() if combo else 'Canny'
            label.setText(f"{name}: {text} ({mode})")
        else:
            label.setText(f"{name}: {text}")
        self.timer.start()

    def on_edge_mode_change(self, name, label):
        # Update label to reflect chosen mode
        chk, combo = self.sliders['Edge']
        state = chk.isChecked()
        text = 'On' if state else 'Off'
        mode = combo.currentText()
        label.setText(f"{name}: {text} ({mode})")
        self.timer.start()

    def fire_callback(self):
        # Panggil callback pas slider digeser (buat mode edit foto biasa)
        params = self.get_params()
        self.callback(params)

    def get_params(self):
        # Kembalikan dict parameter yang cocok dipassing ke worker
        params = {}
        for name, widget in self.sliders.items():
            key = name.lower()
            # Slider
            if isinstance(widget, QtWidgets.QSlider):
                params[key] = float(widget.value())
            # Checkbox only (invert)
            elif isinstance(widget, QtWidgets.QCheckBox):
                params[key] = 1.0 if widget.isChecked() else 0.0
            # Edge stored as tuple (checkbox, combo)
            elif isinstance(widget, tuple) or isinstance(widget, list):
                chk, combo = widget
                params[key] = 1.0 if chk.isChecked() else 0.0
                params[f"{key}_mode"] = combo.currentText().lower()
            # QComboBox direct (fallback)
            elif isinstance(widget, QtWidgets.QComboBox):
                params[key] = widget.currentText().lower()
            else:
                # Unknown widget, attempt to get .value() gracefully
                try:
                    params[key] = float(widget.value())
                except Exception:
                    params[key] = 0.0
        return params

    def set_params(self, params: dict):
        # Set widget values based on a params dict (used for undo/redo restore)
        if not params: return
        for name, widget in list(self.sliders.items()):
            key = name.lower()
            if isinstance(widget, QtWidgets.QSlider):
                val = int(params.get(key, 0))
                widget.blockSignals(True)
                widget.setValue(val)
                widget.blockSignals(False)
                self.labels[name].setText(f"{name}: {val}")
            elif isinstance(widget, QtWidgets.QCheckBox):
                val = bool(params.get(key, 0))
                widget.blockSignals(True)
                widget.setChecked(val)
                widget.blockSignals(False)
                self.labels[name].setText(f"{name}: {'On' if val else 'Off'}")
            elif isinstance(widget, tuple) or isinstance(widget, list):
                chk, combo = widget
                val = bool(params.get(key, 0))
                mode = params.get(f"{key}_mode", combo.currentText().lower())
                chk.blockSignals(True)
                combo.blockSignals(True)
                chk.setChecked(val)
                # set combo to matching text if present
                idx = combo.findText(mode.capitalize())
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                chk.blockSignals(False)
                combo.blockSignals(False)
                self.labels[name].setText(f"{name}: {'On' if val else 'Off'} ({combo.currentText()})")

    def reset(self):
        for k, s in list(self.sliders.items()):
            if isinstance(s, QtWidgets.QSlider):
                s.blockSignals(True)
                s.setValue(0)
                s.blockSignals(False)
                self.labels[k].setText(f"{k}: 0")
            elif isinstance(s, QtWidgets.QCheckBox):
                s.blockSignals(True)
                s.setChecked(False)
                s.blockSignals(False)
                self.labels[k].setText(f"{k}: Off")
            elif isinstance(s, tuple) or isinstance(s, list):
                chk, combo = s
                chk.blockSignals(True)
                combo.blockSignals(True)
                chk.setChecked(False)
                combo.setCurrentIndex(0)
                chk.blockSignals(False)
                combo.blockSignals(False)
                self.labels[k].setText(f"{k}: Off ({combo.currentText()})")