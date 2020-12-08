#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
This example demonstrates many of the 2D plotting capabilities
in pyqtgraph. All of the plots may be panned/scaled by dragging with 
the left/right mouse buttons. Right click on any plot to show a context menu.
"""

"""
Demonstrates use of PlotWidget class. This is little more than a 
GraphicsView with a PlotItem placed in its center.
"""


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import serial
from time import sleep

from emg.mtpkit.driver import UnoDriver 
from emg.mtpkit.gui import ScopeGui


n_samples = 600
v_ref = 5
chan1_delay = 1.0 / 76900  # a single adc conversion at prescaler = 16

times = np.linspace(0, 100e-3, n_samples)  # TODO correct adc delay
data0 = np.full(n_samples, np.nan)
data1 = np.full(n_samples, np.nan)
xy = False

config_queue = []

""" 

    graph_update()
    data_update()


def graph_update():
    global pw

    pw.setLabel("left", "Value", units="V")
    pw.setLabel("bottom", "Time", units="s")
    pw.setXRange(0, 100e-3)
    pw.setYRange(0, 5)
    pw.showGrid(x=True, y=True, alpha=0.3)


def data_update():
    global xy, times, data0, data1, chan0, chan1
    if xy:
        chan0.setVisible(True)
        chan1.setVisible(False)
        chan1.setData(y=data1, x=data0)
    else:
        chan0.setVisible(True)
        chan1.setVisible(True)

        chan0.setData(y=data0, x=times + chan1_delay)
        chan1.setData(y=data1, x=times)


def config_send():
    pass


def serial_poll():
    global ser, data0, data1

    if ser is None or not ser.is_open:
        return

    header_size = 4
    aux_size = 0
    packet_size = header_size + aux_size + n_samples * 2
    
    if ser.in_waiting >= packet_size:
        packet = ser.read(packet_size)
        assert len(packet) == packet_size
        packet = np.frombuffer(packet, dtype=np.uint8)

        if not np.array_equal(packet[:header_size], [0x00, 0x00, 0xFF, 0xFF]):
            print(packet[:header_size])
            data0[:] = np.nan
            data1[:] = np.nan
            graph_update()

            serial_init()  # sync lost
            return
        
        # TODO parse aux

        # convert data
        data = (
            packet[header_size + aux_size :].astype(np.float32).reshape((2, n_samples))
        )
        data0 = data[0,:] / 0xFF * v_ref
        data1 = data[1,:] / 0xFF * v_ref
        print(data)
        data_update()

    if config_queue:
        pass
    else:
        # just send ack
        ser.write(b'\0')


def serial_init():
    global ser

    print("No sync or port closed: initializing UART")
    ser = None
    init = serial.Serial(port="/dev/ttyACM0", baudrate=115200)# 57600)#921600)
    init.setDTR(False)
    sleep(0.25)
    init.flushInput()
    init.setDTR(True)
    ser = init

""" 

if __name__ == "__main__":
    import sys

    drv = UnoDriver("miau")
    gui = ScopeGui(drv)

    #t = QtCore.QTimer()
    #t.timeout.connect(serial_poll)
    #t.start(5)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtGui.QApplication.instance().exec_()
