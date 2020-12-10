[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# Gruseloskop

Gruseloskop (german worldplay refering to an imagination of having
this as the only tool in your lab) is a simple oscilloscope GUI for Arduino Uno. 

> **Companion Arduino Uno sketch must be manually flashed using [Arduino IDE][arduino]**
> You can find the sketch under [firmware][firmware]. 

![](https://raw.githubusercontent.com/EvilMav/gruseloskop/master/screenshot.gif) 

This is a project hacked together over a weekend and is not regularly maintained. 
Keep bleach closely available at all times to wash you eyes in case you accidentally see
the source code. Consider yourself lucky if you find a comment there.

## Installation

### On Linux :penguin:

First, ensure that [Qt][qt] is installed using your distribution's package manager. 
Use `pip` to install the GUI, note that it will automatically install [PySide2][pyside] 
Qt bindings.

```sh
pip install git+https://github.com/EvilMav/gruseloskop.git
```

### On Windows :scream:

Unless you have python installed, you can grab a latest stand-alone binary package, 
named something like `gruseloskop-x.x.x-win64.7z`, under
[releases][releases]. It is ridiculously big, containing a large part of the Python 
distribution, but it does not require any setup. 

### Firmware

Connect you Arduino Uno and use the IDE to compile and install the [firmware][firmware].
`TimerOne` library must be installed for this to compile, which can be done in the IDE
using *Sketch->Include Library->Manage Libraries...* menu.

## Usage

Simply launch `gruseloskop` from the command line (or doubleclick `gruseloskop.exe` 
on Windows) with Arduino connected. It will automatically detect the correct serial 
port by the currently hardcoded *VID:PID* pair.

## Capabilities

Currently, selectable edge triggers are supported. After each trigger, the arduino will 
sample `A0` and `A1` channels with 8 bit, filling 800 sample buffer. The sample rate is 
chosen such that at least one screen of the GUI is filled, achieving a maximum of about
38.4kHz at sufficiently low time bases. Pin 9 can be used as a 5V rectangle wave 
generator output with selectable frequency between 1Hz and 5kHz. 

Be careful with the voltages: to achieve a 5V input range the Vcc of the Board is used 
as the **reference voltage**. When connected to USB only, this is subject to an 
**USB supply tolerance of up to 10%!** When connected to an external supply, the 
on-board linear regulator will likely provide more reproducible results, so use it when
possible.

## Contributing

Feel free to fork and submit pull requests. Any python code checked in must be 
formated using [Black][black], which forces PEP8 but with 88 columns rather then 80.

[arduino]: https://www.arduino.cc/en/software
[firmware]: https://github.com/EvilMav/gruseloskop/tree/master/firmware
[releases]: https://github.com/EvilMav/gruseloskop/releases/
[qt]: https://www.qt.io/
[pyside]: https://wiki.qt.io/Qt_for_Python
[black]: https://black.readthedocs.io/en/stable/