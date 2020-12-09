#!/usr/bin/env python3

import sys
import argparse
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

from gruseloskop.driver import UnoDriver
from gruseloskop.gui import ScopeGui

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "--dummy",
    dest="dummy",
    action="store_true",
    help="Emulator mode for UI testing without hardware",
)


def die(msg):
    QtGui.QMessageBox.critical(None, "Failed to run", msg)
    sys.exit(-1)


if __name__ == "__main__":
    args = parser.parse_args()

    app = pg.mkQApp()  # must come before driver init

    if args.dummy:
        drv = UnoDriver("dummy")
    else:
        devices = list(UnoDriver.find_devices())
        if not devices:
            die("No Arduino Uno found")

        if len(devices) > 1:
            die(
                "Too many boards found and I'm too lazy to implement a selection dialog"
            )

        drv = UnoDriver(devices[0])
    gui = ScopeGui(drv)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtGui.QApplication.instance().exec_()
