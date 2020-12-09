import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np

from .driver import Config, TriggerMode, TriggerEdge


class ScopeGui:
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
        self._mw.setWindowTitle("MTP Gruselloskop")
        self._mw.resize(800, 800)

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

        self._gb_sgen = QtGui.QGroupBox("Signal generator")
        self._gb_sgen.setCheckable(True)
        self._gb_sgen.setLayout(self._sgen_controls_create())

        self._gb_vertical_a0.toggled.connect(self._control_changed)
        self._gb_vertical_a1.toggled.connect(self._control_changed)
        self._gb_sgen.toggled.connect(self._control_changed)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(gb_trig)
        layout.addWidget(gb_horizontal)
        layout.addWidget(self._gb_vertical_a0)
        layout.addWidget(self._gb_vertical_a1)
        layout.addWidget(self._gb_sgen)
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

        self._bg_trig_mode.idToggled.connect(self._control_changed)
        self._bg_trig_src.idToggled.connect(self._control_changed)
        self._bg_trig_edge.idToggled.connect(self._control_changed)
        self._sld_trig_lvl.valueChanged.connect(self._trig_lvl_changed)

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

    def _sgen_controls_create(self):
        lbl0 = QtGui.QLabel("Offset: 2.5V, Vpp=5V")
        lbl1 = QtGui.QLabel("1kHz")
        layout = QtGui.QVBoxLayout()
        layout.addWidget(lbl0)
        layout.addWidget(lbl1)
        return layout

    def _crt_ax_update(self):
        vmin, vmax = 0.0, 5.0

        if self.xy_mode:
            self._crt.setXRange(0, 5)
            self._crt_axis_set("bottom", vmin, vmax, ScopeGui._volt_divs)
        else:
            tmax = self.divtime * ScopeGui._time_divs
            self._crt.setXRange(0, tmax)
            self._crt_axis_set("bottom", 0.0, tmax, ScopeGui._time_divs)

        self._crt.setYRange(0, 5)
        self._crt_axis_set("left", vmin, vmax, ScopeGui._volt_divs)

    def _trig_lvl_changed(self, source):
        # reserved for drawing trigger level line later
        self._control_changed(source)

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

    def _gather_drv_config(self):
        cfg = Config()
        cfg.trig_mode = self._bg_trig_mode.checkedId()
        cfg.trig_level = self._sld_trig_lvl.value() / 100 * 5.0
        cfg.trig_chan = self._bg_trig_src.checkedId()
        cfg.trig_edge = self._bg_trig_edge.checkedId()
        cfg.timeframe = self.divtime * ScopeGui._time_divs
        cfg.sgen_freq = 1000 if self._gb_sgen.isChecked() else 0
        return cfg

    def _control_changed(self, source):
        self._crt_ax_update()
        self._drv_update(self._last_data)
        self._driver.set_config(self._gather_drv_config())
