import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QFileDialog, QLineEdit,
    QTextEdit, QProgressBar, QCheckBox, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from gps_navigation import (
    parse_rinex_nav, get_time_bounds, generate_time_sequence,
    compute_positions, write_csv
)
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class GNSSGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" GNSS Orbit Processor")
        self.resize(1200, 800)
        self.nav_data = {}
        self.current_file = None
        self.output_dir = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        central.setLayout(layout)

        left_panel = QVBoxLayout()
        layout.addLayout(left_panel, 1)

        file_layout = QHBoxLayout()
        self.lbl_file = QLabel("No file loaded")
        btn_browse = QPushButton(" Load RINEX File")
        btn_browse.clicked.connect(self.load_file)
        file_layout.addWidget(btn_browse)
        file_layout.addWidget(self.lbl_file)
        left_panel.addLayout(file_layout)

        left_panel.addWidget(QLabel("Available PRNs:"))
        self.prn_list = QListWidget()
        self.prn_list.setSelectionMode(QListWidget.MultiSelection)
        left_panel.addWidget(self.prn_list)

        left_panel.addWidget(QLabel("Options:"))
        self.cb_csv = QCheckBox("Save CSV Output")
        self.cb_csv.setChecked(True)
        self.cb_plot = QCheckBox("Show 3D Plot")
        self.cb_plot.setChecked(True)
        left_panel.addWidget(self.cb_csv)
        left_panel.addWidget(self.cb_plot)

        dt_layout = QHBoxLayout()
        dt_layout.addWidget(QLabel("Sample Δt (s):"))
        self.input_dt = QLineEdit("30")
        dt_layout.addWidget(self.input_dt)
        left_panel.addLayout(dt_layout)

        self.btn_process = QPushButton(" Process Selected PRNs")
        self.btn_process.clicked.connect(self.process_selected)
        left_panel.addWidget(self.btn_process)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        left_panel.addWidget(self.progress)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(200)
        left_panel.addWidget(self.log)

        right_panel = QVBoxLayout()
        layout.addLayout(right_panel, 3)
        self.fig = Figure(figsize=(5,5))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_panel.addWidget(self.canvas)

    def log_msg(self, txt):
        self.log.append(txt)
        self.log.ensureCursorVisible()

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select RINEX Navigation File", "", "RINEX Files (*.rnx *.yyN *.nav);;All Files (*)"
        )
        if not fname:
            return
        try:
            self.nav_data = parse_rinex_nav(fname)
            self.current_file = fname
            self.lbl_file.setText(os.path.basename(fname))
            self.prn_list.clear()
            for prn in sorted(self.nav_data.keys()):
                self.prn_list.addItem(prn)
            self.log_msg(f" Loaded '{fname}' with {len(self.nav_data)} PRNs.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse file:\n{e}")
            self.log_msg(f" Error loading file: {e}")

    def process_selected(self):
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please load a RINEX nav file first.")
            return
        selected = [it.text() for it in self.prn_list.selectedItems()]
        if not selected:
            QMessageBox.warning(self, "No PRNs", "Please select at least one PRN to process.")
            return

        if self.cb_csv.isChecked():
            d = QFileDialog.getExistingDirectory(self, "Select Output Directory", os.getcwd())
            if not d:
                return
            self.output_dir = d

        if self.cb_plot.isChecked():
            self.fig.clear()
            ax = self.fig.add_subplot(111, projection='3d')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_zlabel('Z (m)')
            ax.set_title('Satellite Trajectories')
        else:
            ax = None

        try:
            dt = float(self.input_dt.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Δt", "Sampling interval must be a number.")
            return

        self.progress.setMinimum(0)
        self.progress.setMaximum(len(selected))
        self.progress.setValue(0)

        for idx, prn in enumerate(selected, start=1):
            self.log_msg(f" Processing PRN {prn}...")
            records = self.nav_data[prn]
            start, end = get_time_bounds(records)
            times = generate_time_sequence(start, end, dt)
            coords = compute_positions(records, times)

            if self.cb_csv.isChecked():
                out_name = os.path.join(self.output_dir, f"output_{prn}.csv")
                write_csv(coords, out_name)
                self.log_msg(f" CSV saved: {out_name}")

            if ax is not None:
                xs, ys, zs = zip(*[(x, y, z) for _, x, y, z in coords])
                ax.plot(xs, ys, zs, label=prn)

            self.progress.setValue(idx)

        if ax is not None:
            ax.legend(loc='upper right')
            self.canvas.draw()

        self.log_msg(" Processing complete!")

def main():
    app = QApplication(sys.argv)
    gui = GNSSGui()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
