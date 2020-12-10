import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from pyqtgraph.functions import mkPen

from .driver import Config, TriggerMode, TriggerEdge


class ScopeGui:
    _vmin = 0.0
    _vmax = 5.0
    _time_divs = 6
    _volt_divs = 5
    _t_div_items = {
        "1s    / DIV": 1.0,
        "0.5s  / DIV": 0.5,
        "200ms / DIV": 0.2,
        "100ms / DIV": 0.1,
        "50ms  / DIV": 0.05,
        "20ms  / DIV": 0.02,
        "10ms  / DIV": 0.01,
        "5ms   / DIV": 0.005,
        "2ms   / DIV": 0.002,
        "1ms   / DIV": 0.001,
    }

    def __init__(self, driver):
        self._driver = driver
        self._last_data = None

        self._ui_setup()
        driver.set_update_callback(self._drv_update)

        self._control_changed(None)

    def _ui_setup(self):

        self._mw = QtGui.QMainWindow()
        self._mw.setWindowTitle("Gruseloskop (feat. Arduino Uno)")
        self._mw.resize(1000, 700)

        cw = QtGui.QWidget()
        self._mw.setCentralWidget(cw)
        l = QtGui.QGridLayout()
        cw.setLayout(l)

        l.addWidget(self._crt_create(), 0, 1, 1, 1)
        l.addLayout(self._controls_create(), 0, 0, 2, 1)
        l.addWidget(self._stats_create(), 1, 1, 1, 1)

        self._mw.show()

    def _crt_create(self):
        self._crt = pg.PlotWidget(name="Scope")
        self._crt.setMouseEnabled(x=False, y=False)
        self._crt.setMenuEnabled(False)
        self._crt.showGrid(x=True, y=True, alpha=0.3)

        pg.setConfigOptions(antialias=True, leftButtonPan=False)

        self._plot0 = self._crt.plot()
        self._plot0.setPen((200, 200, 100))

        self._plot1 = self._crt.plot()
        self._plot1.setPen((000, 200, 100))

        # cursors for trigger and measurements
        pen_curtrig = mkPen("b", style=QtCore.Qt.DotLine)
        pen_cur0 = mkPen("r", style=QtCore.Qt.DashLine)
        pen_cur1 = mkPen("y", style=QtCore.Qt.DashLine)

        self._cursor_trig = pg.InfiniteLine(2.5, 0, pen_curtrig, movable=False)
        self._cursor_trig.hide()

        self._cursor0 = pg.InfiniteLine(2.5, 0, pen_cur0, True, label="")
        self._cursor1 = pg.InfiniteLine(2.5, 0, pen_cur1, True, label="")

        self._cursor_trig.hide()
        self._cursor0.hide()
        self._cursor1.hide()

        self._cursor0.sigPositionChanged.connect(self._cursor_moved)
        self._cursor1.sigPositionChanged.connect(self._cursor_moved)

        self._crt.addItem(self._cursor_trig)
        self._crt.addItem(self._cursor0)
        self._crt.addItem(self._cursor1)

        return self._crt

    def _crt_axis_set(self, name, minval, maxval, divs_num):
        divs = np.linspace(minval, maxval, divs_num + 1, endpoint=True)
        ticks = np.linspace(minval, maxval, divs_num * 10 + 1, endpoint=True)

        ax = self._crt.getAxis(name)
        ax.setTicks([[(d, "") for d in divs], [(t, "") for t in ticks]])

    def _controls_create(self):
        gb_trig = QtGui.QGroupBox("Trigger")
        gb_trig.setLayout(self._trigger_controls_create())

        gb_horizontal = QtGui.QGroupBox("Horizontal")
        gb_horizontal.setLayout(self._horizontal_controls_create())

        self._gb_vertical_a0 = QtGui.QGroupBox("Vertical A0")
        self._gb_vertical_a0.setCheckable(True)
        self._gb_vertical_a0.setStyleSheet(
            "QGroupBox:title {color: rgb(200, 200, 100);}"
        )
        self._gb_vertical_a0.setLayout(self._vertical_controls_create(0))

        self._gb_vertical_a1 = QtGui.QGroupBox("Vertical A1")
        self._gb_vertical_a1.setCheckable(True)
        self._gb_vertical_a1.setStyleSheet("QGroupBox:title {color: rgb(0, 200, 100);}")
        self._gb_vertical_a1.setLayout(self._vertical_controls_create(1))

        self._gb_sgen = QtGui.QGroupBox("Signal generator (Pin 9)")
        self._gb_sgen.setCheckable(True)
        self._gb_sgen.setChecked(False)
        self._gb_sgen.setLayout(self._sgen_controls_create())

        self._gb_cursors = QtGui.QGroupBox("Cursors")
        self._gb_cursors.setCheckable(True)
        self._gb_cursors.setChecked(False)
        self._gb_cursors.setLayout(self._cursor_controls_create())

        self._gb_vertical_a0.toggled.connect(self._control_changed)
        self._gb_vertical_a1.toggled.connect(self._control_changed)
        self._gb_sgen.toggled.connect(self._control_changed)
        self._gb_cursors.toggled.connect(self._cursors_changed)

        self._gb_export = QtGui.QGroupBox("Export")
        self._gb_export.setLayout(self._export_controls_create())

        self._gb_author = QtGui.QGroupBox("Author")
        self._gb_author.setLayout(self._author_controls_create())

        layout = QtGui.QVBoxLayout()
        layout.addWidget(gb_trig)
        layout.addWidget(gb_horizontal)
        layout.addWidget(self._gb_vertical_a0)
        layout.addWidget(self._gb_vertical_a1)
        layout.addWidget(self._gb_cursors)
        layout.addWidget(self._gb_sgen)
        layout.addWidget(self._gb_export)
        layout.addWidget(self._gb_author)
        return layout

    def _stats_create(self):
        self._lbl_stats = QtGui.QLabel()
        self._lbl_stats.setAlignment(QtCore.Qt.AlignRight)
        self._lbl_stats.setText("Signal statistics")
        return self._lbl_stats

    def _trigger_controls_create(self):
        rb_trig_auto = QtGui.QRadioButton("Auto")
        rb_trig_norm = QtGui.QRadioButton("Norm")
        rb_trig_stop = QtGui.QRadioButton("Stop")
        rb_trig_auto.setChecked(True)

        self._bg_trig_mode = QtGui.QButtonGroup()
        self._bg_trig_mode.addButton(rb_trig_auto, TriggerMode.AUTO)
        self._bg_trig_mode.addButton(rb_trig_norm, TriggerMode.NORM)
        self._bg_trig_mode.addButton(rb_trig_stop, TriggerMode.STOP)

        rb_trig_src0 = QtGui.QRadioButton("A0")
        rb_trig_src1 = QtGui.QRadioButton("A1")
        rb_trig_src0.setChecked(True)

        self._bg_trig_src = QtGui.QButtonGroup()
        self._bg_trig_src.addButton(rb_trig_src0, 0)
        self._bg_trig_src.addButton(rb_trig_src1, 1)

        self._sld_trig_lvl = QtGui.QSlider(QtCore.Qt.Horizontal)
        self._sld_trig_lvl.setTracking(True)
        self._sld_trig_lvl.setValue(50)

        rb_trig_edge_raising = QtGui.QRadioButton("Raising")
        rb_trig_edge_falling = QtGui.QRadioButton("Falling")
        rb_trig_edge_both = QtGui.QRadioButton("Both")
        rb_trig_edge_raising.setChecked(True)

        self._bg_trig_edge = QtGui.QButtonGroup()
        self._bg_trig_edge.addButton(rb_trig_edge_raising, TriggerEdge.RAISING)
        self._bg_trig_edge.addButton(rb_trig_edge_falling, TriggerEdge.FALLING)
        self._bg_trig_edge.addButton(rb_trig_edge_both, TriggerEdge.BOTH)

        self._bg_trig_mode.buttonClicked.connect(self._control_changed)
        self._bg_trig_src.buttonClicked.connect(self._control_changed)
        self._bg_trig_edge.buttonClicked.connect(self._control_changed)
        self._sld_trig_lvl.valueChanged.connect(self._trig_lvl_changed)

        # timer for hiding trigger helper cursor
        self._trig_cursor_timer = QtCore.QTimer()
        self._trig_cursor_timer.setSingleShot(True)
        self._trig_cursor_timer.timeout.connect(self._cursor_trig.hide)

        layout = QtGui.QGridLayout()
        layout.addWidget(rb_trig_auto, 0, 0, 1, 1)
        layout.addWidget(rb_trig_norm, 0, 1, 1, 1)
        layout.addWidget(rb_trig_stop, 0, 2, 1, 1)

        layout.addWidget(QtGui.QLabel("Source:"), 1, 0, 1, 1)
        layout.addWidget(rb_trig_src0, 1, 1, 1, 1)
        layout.addWidget(rb_trig_src1, 1, 2, 1, 1)

        layout.addWidget(QtGui.QLabel("Level:"), 2, 0, 1, 1)
        layout.addWidget(self._sld_trig_lvl, 2, 1, 1, 2)

        layout.addWidget(rb_trig_edge_raising, 3, 0, 1, 1)
        layout.addWidget(rb_trig_edge_falling, 3, 1, 1, 1)
        layout.addWidget(rb_trig_edge_both, 3, 2, 1, 1)

        return layout

    def _vertical_controls_create(self, chan):
        lbl = QtGui.QLabel("1V / DIV")
        layout = QtGui.QVBoxLayout()
        layout.addWidget(lbl)
        return layout

    def _horizontal_controls_create(self):
        self._cmb_t_div = pg.ComboBox(
            items=ScopeGui._t_div_items,
            default=list(ScopeGui._t_div_items.values())[-1],
        )
        self._cmb_t_div.currentIndexChanged.connect(self._control_changed)

        self._rb_xy_ty = QtGui.QRadioButton("t-Y")
        self._rb_xy_a0a1 = QtGui.QRadioButton("X-Y (X=A0, Y=A1)")
        self._rb_xy_a0a10 = QtGui.QRadioButton("X-Y (X=A0, Y=A1-A0)")
        self._rb_xy_ty.setChecked(True)

        self._rb_xy_ty.toggled.connect(self._control_changed)
        self._rb_xy_a0a1.toggled.connect(self._control_changed)
        self._rb_xy_a0a10.toggled.connect(self._control_changed)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._cmb_t_div)
        layout.addWidget(self._rb_xy_ty)
        layout.addWidget(self._rb_xy_a0a1)
        layout.addWidget(self._rb_xy_a0a10)
        return layout

    def _cursor_controls_create(self):
        self._rb_cursors_horizontal = QtGui.QRadioButton("Horizontal")
        self._rb_cursors_vertical = QtGui.QRadioButton("Vertical")
        self._rb_cursors_horizontal.setChecked(True)

        self._lbl_cursors = QtGui.QLabel("")

        self._rb_cursors_horizontal.toggled.connect(self._cursors_changed)
        self._rb_cursors_vertical.toggled.connect(self._cursors_changed)

        layout = QtGui.QGridLayout()
        layout.addWidget(self._rb_cursors_horizontal, 0, 0, 1, 1)
        layout.addWidget(self._rb_cursors_vertical, 0, 1, 1, 1)
        layout.addWidget(self._lbl_cursors, 1, 0, 1, 2)
        return layout

    def _sgen_controls_create(self):
        lbl0 = QtGui.QLabel("Rect: Offset=2.5V, Vpp=5V")

        self._sb_sgen_freq = pg.SpinBox(value=1000)
        self._sb_sgen_freq.setOpts(
            bounds=(1, 5000), suffix="Hz", siPrefix=True, step=0.5, dec=True, minStep=1
        )

        self._sb_sgen_freq.valueChanged.connect(self._control_changed)
        self._sb_sgen_freq.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        )
        self._sb_sgen_freq.setFixedHeight(25)  # too small on PySide2 by default

        layout = QtGui.QVBoxLayout()
        layout.addWidget(lbl0)
        layout.addWidget(self._sb_sgen_freq)
        return layout

    def _export_controls_create(self):
        self._btn_export_csv = QtGui.QPushButton("To CSV")
        self._btn_export_csv.clicked.connect(self._export_csv)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._btn_export_csv)
        return layout

    def _author_controls_create(self):
        repo = '<a href="https://github.com/EvilMav/gruseloskop">GitHub repository</a>'

        label = QtGui.QLabel("Ilya Elenskiy<br/>i.elenskiy@tu-bs.de<br/>" + repo)
        label.setAlignment(QtGui.Qt.AlignCenter)
        label.setTextFormat(QtGui.Qt.RichText)
        label.setTextInteractionFlags(QtGui.Qt.TextBrowserInteraction)
        label.setOpenExternalLinks(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        return layout

    def _crt_ax_update(self):

        if self.xy_mode:
            self._crt.setXRange(0, 5)
            self._crt_axis_set(
                "bottom", ScopeGui._vmin, ScopeGui._vmax, ScopeGui._volt_divs
            )
        else:
            tmax = self.divtime * ScopeGui._time_divs
            self._crt.setXRange(0, tmax)
            self._crt_axis_set("bottom", 0.0, tmax, ScopeGui._time_divs)

        self._crt.setYRange(ScopeGui._vmin, ScopeGui._vmax)
        self._crt_axis_set("left", ScopeGui._vmin, ScopeGui._vmax, ScopeGui._volt_divs)

    def _crt_data_update(self, data):
        if data is None:
            self._plot0.setVisible(False)
            self._plot1.setVisible(False)
            self._plot0.setData(y=[], x=[])
            self._plot1.setData(y=[], x=[])
            return

        if self.xy_mode:
            self._plot0.setVisible(False)
            self._plot1.setVisible(True)
            if self.xy_mode == "A1":
                self._plot1.setData(y=data.data1, x=data.data0)
            elif self.xy_mode == "A1-A0":
                self._plot1.setData(y=data.data1 - data.data0, x=data.data0)
            else:
                self._plot1.setData(y=[], x=[])
        else:
            self._plot0.setVisible(self._gb_vertical_a0.isChecked())
            self._plot1.setVisible(self._gb_vertical_a1.isChecked())

            self._plot0.setData(y=data.data0, x=data.time0)
            self._plot1.setData(y=data.data1, x=data.time1)

    def _stats_data_update(self, data):
        if data is None:
            self._lbl_stats.setText("NO DATA")
            return

        a0avg = np.mean(data.data0)
        a0pp = np.max(data.data0) - np.min(data.data0)
        a1avg = np.mean(data.data1)
        a1pp = np.max(data.data1) - np.min(data.data1)
        stat_a0 = "A0: Vavg={:04.3f}V, Vpp={:04.3f}V; ".format(a0avg, a0pp)
        stat_a1 = "A1: Vavg={:04.3f}V, Vpp={:04.3f}V; ".format(a1avg, a1pp)

        spl_rate_hint = "Sample rate: {:06.3f}kHz; ".format(data.spl_rate / 1000)
        self._lbl_stats.setText(stat_a0 + stat_a1 + spl_rate_hint)

    def _drv_update(self, data):
        self._last_data = data
        self._crt_data_update(data)
        self._stats_data_update(data)

    @property
    def divtime(self):
        return self._cmb_t_div.value()

    @property
    def xy_mode(self):
        if self._rb_xy_a0a1.isChecked():
            return "A1"
        elif self._rb_xy_a0a10.isChecked():
            return "A1-A0"
        else:
            return False

    @property
    def trig_level(self):
        return self._sld_trig_lvl.value() / 99 * ScopeGui._vmax

    @property
    def cursors_mode(self):
        if self.xy_mode or self._rb_cursors_horizontal.isChecked():
            return "voltage"
        else:
            return "time"

    def _gather_drv_config(self):
        cfg = Config()
        cfg.trig_mode = self._bg_trig_mode.checkedId()
        cfg.trig_level = self.trig_level
        cfg.trig_chan = self._bg_trig_src.checkedId()
        cfg.trig_edge = self._bg_trig_edge.checkedId()
        cfg.timeframe = self.divtime * ScopeGui._time_divs
        cfg.sgen_freq = self._sb_sgen_freq.value() if self._gb_sgen.isChecked() else 0.0
        return cfg

    def _cursor_moved(self, source):
        if self._gb_cursors.isChecked():
            c0, c1 = self._cursor0.value(), self._cursor1.value()

            if self.cursors_mode == "voltage":
                self._lbl_cursors.setText("ΔV={:4.3f}V".format(c1 - c0))
            else:
                dt = np.abs(c1 - c0)
                freq = 1.0 / dt if dt != 0 else np.inf
                dt_text = (
                    "Δt={:0.3f}s".format(dt)
                    if dt >= 1.0
                    else "Δt={:0.2f}ms".format(dt * 1e3)
                )
                freq_text = (
                    "1/Δt={:0.2f}kHz".format(freq * 1e-3)
                    if freq >= 1e3
                    else "1/Δt={:0.2f}Hz".format(freq)
                )
                self._lbl_cursors.setText(dt_text + "  " + freq_text)
        else:
            self._lbl_cursors.setText("")

    def _trig_lvl_changed(self, source):
        # reserved for drawing trigger level line later
        self._trig_cursor_timer.stop()
        self._trig_cursor_timer.start(1500)
        self._cursor_trig.setValue(self.trig_level)
        self._cursor_trig.show()

        self._control_changed(source)

    def _cursors_changed(self, source):
        if self.cursors_mode == "voltage":
            bounds = (ScopeGui._vmin, ScopeGui._vmax)
            angle = 0 if self._rb_cursors_horizontal.isChecked() else 90
            self._cursor0.label.setFormat("V0={value:0.2f}V")
            self._cursor1.label.setFormat("V1={value:0.2f}V")

        else:
            bounds = (0.0, self.divtime * ScopeGui._time_divs)
            angle = 90
            if self.divtime >= 0.1:
                self._cursor0.label.setFormat("t0={value:0.2f}s")
                self._cursor1.label.setFormat("t1={value:0.2f}s")
            else:
                self._cursor0.label.setFormat("t0={value:0.4f}s")
                self._cursor1.label.setFormat("t1={value:0.4f}s")

        self._cursor0.setBounds(bounds)
        self._cursor1.setBounds(bounds)
        self._cursor0.setAngle(angle)
        self._cursor1.setAngle(angle)

        if self._gb_cursors.isChecked():
            self._cursor0.show()
            self._cursor1.show()
        else:
            self._cursor0.hide()
            self._cursor1.hide()

        self._cursor_moved(None)  # Update calculated values

    def _control_changed(self, source):
        self._crt_ax_update()
        self._drv_update(self._last_data)
        self._driver.set_config(self._gather_drv_config())
        self._cursors_changed(None)

    def _export_csv(self):
        backup = self._last_data
        if backup is None:
            return  # nothing to save yet

        filename, _ = QtGui.QFileDialog.getSaveFileName(
            self._mw,
            "Save CSV",
            "gruseloskop_export.csv",
            "CSV Files (*.csv)",
            options=QtGui.QFileDialog.DontUseNativeDialog,
        )

        if filename is not None:
            data = np.transpose(
                [
                    backup.time0,
                    backup.data0,
                    backup.time1,
                    backup.data1,
                ]
            )
            np.savetxt(filename, data, delimiter=",", header="t0, a0, t1, a1")
