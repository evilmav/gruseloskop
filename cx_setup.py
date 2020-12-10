import sys
import cx_Freeze as cx
from setup import setup_args


build_exe_options = {
    "packages": ["os", "numpy", "pyqtgraph", "PySide2"],
    "includes": "cProfile",
    "excludes": ["tkinter", "PyQt5", "PyQt4"],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

cx.setup(
    **setup_args,
    options={"build_exe": build_exe_options},
    executables=[
        cx.Executable(
            "bin/gruseloskop.py",
            targetName="gruseloskop.exe",
            shortcutName="Gruseloskop",
            base=base,
        )
    ]
)
