import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
includes = ["threading", "multiprocessing", "collections", "time", "nltk", "urllib", "bs4", "re", "sys", "string", "simplejson", "copy", "webbrowser", "tkinter"]
include_files = ["english.pickle"]

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "NetTotal",
        version = "1.0",
        description = "NetTotal by Evan Tam 2015",
            options = {"build_exe": {"includes": includes, "include_files": include_files}},
        executables = [Executable("NetTotal.py", base=base)])
