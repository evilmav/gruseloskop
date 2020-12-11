import sys
import cx_Freeze as cx
from setup import setup_args


build_exe_options = {
    "packages": ["os", "numpy", "pyqtgraph", "PySide2"],
    "includes": "cProfile",
    "excludes": ["tkinter", "PyQt5", "PyQt4", "pyqtgraph.examples"],
}


shortcut_table = [
    (
        "DesktopShortcut",  # Shortcut
        "DesktopFolder",  # Directory_
        "Gruseloskop",  # Name
        "TARGETDIR",  # Component_
        "[TARGETDIR]gruseloskop.exe",  # Target
        None,  # Arguments
        None,  # Description
        None,  # Hotkey
        None,  # Icon
        None,  # IconIndex
        None,  # ShowCmd
        "TARGETDIR",  # WkDir
    ),
]

msi_data = {"Shortcut": shortcut_table}
bdist_msi_options = {"data": msi_data}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

cx.setup(
    **setup_args,
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=[
        cx.Executable(
            "bin/gruseloskop",
            targetName="gruseloskop.exe",
            shortcutName="Gruseloskop",
            shortcutDir="StartMenuFolder",
            base=base,
        )
    ]
)
