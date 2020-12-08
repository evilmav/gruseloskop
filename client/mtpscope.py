#!/usr/bin/env python3

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

from emg.mtpkit.driver import UnoDriver
from emg.mtpkit.gui import ScopeGui


if __name__ == "__main__":
    import sys
    
    app = pg.mkQApp()
    drv = UnoDriver("dummy")
    gui = ScopeGui(drv)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtGui.QApplication.instance().exec_()
