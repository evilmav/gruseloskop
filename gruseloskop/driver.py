from dataclasses import dataclass
from enum import IntEnum
from serial import Serial
from serial.tools import list_ports
from pyqtgraph.Qt import QtCore
import numpy as np
from time import sleep


class TriggerMode(IntEnum):
    AUTO = 0
    NORM = 1
    STOP = 2

class TriggerEdge(IntEnum):
    RAISING = 0
    FALLING = 1
    BOTH = 2

@dataclass
class Config:
    trig_mode: TriggerMode = TriggerMode.AUTO
    trig_level: float = 2.5
    trig_chan: int = 0
    trig_edge: TriggerEdge = TriggerEdge.RAISING
    timeframe: float = 0.1
    sgen_freq: float = 0


@dataclass
class FrameData:
    time0: np.ndarray
    time1: np.ndarray
    data0: np.ndarray
    data1: np.ndarray
    triggered: bool
    spl_rate: float

    @staticmethod
    def packet_size(chan_samples):
        header_size = 4
        aux_size = 1
        return header_size + aux_size + chan_samples * 2


class UnoDriver:
    _device_pid = 67
    _device_vid = 9025
    _poll_delay_ms = 5
    _serial_baud = 115200

    _vref = 5.0
    _chan_samples = 800
    
    _sample_base_clk = 76900 // 2  # max sample rate with 2 channels
    _channel1_delay = 1.0 / 76900  # maximum theoretical rate between samples

    _syncword = [0x00, 0x00, 0xFF, 0xFF]

    @staticmethod
    def find_devices():
        for port in list_ports.comports():
            if port.pid == UnoDriver._device_pid and port.vid == UnoDriver._device_vid:
                yield port.device

    def __init__(self, port):
        self._dummy_mode = port == "dummy"

        self._port = port
        self._ser = None
        self._upd_callback = None
        self._last_config = Config()
        self._config_queue = None

        self._packet_size = FrameData.packet_size(UnoDriver._chan_samples)

        self._poll_timer = QtCore.QTimer()
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start(UnoDriver._poll_delay_ms)

        self._serial_init()

    def _serial_init(self):
        if not self._dummy_mode:
            print("No sync or port closed: initializing UART")
            self._ser = None
            init = Serial(port=self._port, baudrate=UnoDriver._serial_baud)
            init.setDTR(False)
            sleep(0.25)
            init.flushInput()
            init.setDTR(True)
            sleep(0.5)          # wait for arduino to become ready to receive config
            self._ser = init

        self._send_apply_config(self._last_config)

    def _parse_acq_packet(self, packet):
        packet = np.frombuffer(packet, dtype=np.uint8)
        data0 = np.empty_like(self._cur_time0)
        data1 = np.empty_like(self._cur_time1)

        sync_size = np.size(self._syncword)

        if not np.array_equal(packet[:sync_size], self._syncword):
            return None

        aux_size = 1
        aux_data = packet[sync_size : sync_size + aux_size]
        triggered = aux_data != 0

        data = (
            packet[sync_size + aux_size :]
            .astype(np.float32)
            .reshape((2, self._chan_samples))
        )
        data0 = data[0, :] / 0xFF * UnoDriver._vref
        data1 = data[1, :] / 0xFF * UnoDriver._vref

        return FrameData(
            self._cur_time0,
            self._cur_time1,
            data0,
            data1,
            triggered,
            self._cur_sample_rate,
        )

    def _get_dummy_dataframe(self):
        data0 = 0.5 * (0.5 + np.random.rand(UnoDriver._chan_samples)) * UnoDriver._vref
        data1 = 0.5 * (0.5 + np.random.rand(UnoDriver._chan_samples)) * UnoDriver._vref
        return FrameData(
            self._cur_time0, self._cur_time1, data0, data1, True, self._cur_sample_rate
        )

    def set_config(self, config):
        assert isinstance(config, Config)
        if (self._last_config is None) or (config != self._last_config):
            self._config_queue = config

    def set_update_callback(self, callback):
        self._upd_callback = callback

    def _config_packet_make(self, config, sample_div, level):
        sgen_period = 0 if config.sgen_freq == 0. else 1.0 / config.sgen_freq
        sgen_period_100us = sgen_period * 10000

        packet = np.empty(9, dtype=np.uint8)
        packet[0] = 0  # begin with 0 sync
        packet[1] = config.trig_mode
        packet[2] = level
        packet[3] = config.trig_chan
        packet[4] = config.trig_edge
        
        # split uint16 for little endian
        packet[5] = (sample_div - 1) % 0xFF
        packet[6] = (sample_div - 1) // 0xFF
        packet[7] = sgen_period_100us % 0xFF  
        packet[8] = sgen_period_100us // 0xFF
        return packet.tobytes()

    def _send_apply_config(self, config):
        time_at_max_rate = UnoDriver._chan_samples / UnoDriver._sample_base_clk
        spl_rate_div = int(np.ceil(config.timeframe / time_at_max_rate))
        trig_level = int(config.trig_level / UnoDriver._vref * 0xFF)

        if not self._dummy_mode and self._ser is not None:
            packet = self._config_packet_make(config, spl_rate_div, trig_level)
            self._ser.write(packet)

        self._cur_sample_rate = UnoDriver._sample_base_clk / spl_rate_div
        self._cur_time0 = np.linspace(
            0, time_at_max_rate * spl_rate_div, UnoDriver._chan_samples
        )
        self._cur_time1 = self._cur_time0 + UnoDriver._channel1_delay
        self._last_config = config

    def _poll(self):
        if self._dummy_mode:
            if (
                self._upd_callback is not None
                and not self._last_config.trig_mode == TriggerMode.STOP
            ):
                self._upd_callback(self._get_dummy_dataframe())
        else:
            if self._ser is None or not self._ser.is_open:
                return

            if self._ser.in_waiting >= self._packet_size:
                packet = self._ser.read(self._packet_size)
                assert len(packet) == self._packet_size

                parsed = self._parse_acq_packet(packet)
                if parsed is None:
                    self._serial_init()  # lost sync or something like that
                elif self._upd_callback is not None:
                    self._upd_callback(parsed)

        if self._config_queue is not None:
            self._send_apply_config(self._config_queue)
            self._config_queue = None
