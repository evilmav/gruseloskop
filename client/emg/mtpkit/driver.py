from dataclasses import dataclass
from enum import Enum
from serial import Serial
import numpy as np


class Trigger(Enum):
    AUTO = 0
    NORM = 1
    STOP = 2

@dataclass 
class Config:
    trig_mode: Trigger 
    trig_level: float
    trig_chan: int
    timeframe: float
    sgen_freq: float 

@dataclass 
class FrameData:
    time0: np.ndarray
    time1: np.ndarray
    data0: np.ndarray
    data1: np.ndarray
    triggered: bool
    spl_rate: float

class UnoDriver:

    @staticmethod
    def find_ports():
        pass  

    def __init__(self, port):
        pass

    def set_config(self, config):
        pass

    def set_update_callback(self, callback):
        pass