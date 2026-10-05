# Installation guide

Photo Sorter supports Windows, macOS, and Linux. Use Python 3.10 or later.
Install Python and its Tkinter GUI support, then create a virtual environment
in the Photo Sorter project folder. The app checks and installs its image
packages at startup; you can also run the updater yourself.

## Windows

1. Install Python 3.10 or later from [python.org](https://www.python.org/downloads/).
   Tkinter is included with the standard Windows installer.
2. Open PowerShell and change to the folder containing `photo_sorter.py`,
   `requirements.txt`, and this guide:

   ```powershell
   cd "C:\path\to\PhotoSorter"
   ```

3. Create the environment, install/check packages, and launch:

   ```powershell
   py -3 -m venv venv_photosorter
   .\venv_photosorter\Scripts\python.exe package_updater.py
   .\venv_photosorter\Scripts\python.exe photo_sorter.py
   ```

If `py` is unavailable, use `python -m venv venv_photosorter` if Python is on
your PATH.

## macOS

1. Install Python 3.10 or later. The official python.org installer includes
   Tkinter. If you use another Python distribution, make sure it includes
   Tcl/Tk support.
2. Open Terminal and change to the Photo Sorter project folder:

   ```sh
   cd /path/to/PhotoSorter
   ```

3. Create the environment, install/check packages, and launch:

   ```sh
   python3 -m venv venv_photosorter
   ./venv_photosorter/bin/python package_updater.py
   ./venv_photosorter/bin/python photo_sorter.py
   ```

## Linux

1. Install Python 3.10 or later, `venv`, and Tkinter using your distribution's
   package manager. For example:

   **Ubuntu/Debian**

   ```sh
   sudo apt update
   sudo apt install python3 python3-venv python3-tk
   ```

   **Fedora**

   ```sh
   sudo dnf install python3 python3-tkinter
   ```

   **Arch Linux**

   ```sh
   sudo pacman -S python tk
   ```

2. Open a terminal and change to the Photo Sorter project folder:

   ```sh
   cd /path/to/PhotoSorter
   ```

3. Create the environment, install/check packages, and launch:

   ```sh
   python3 -m venv venv_photosorter
   ./venv_photosorter/bin/python package_updater.py
   ./venv_photosorter/bin/python photo_sorter.py
   ```

## Notes

- The first package check needs an internet connection if dependencies are
  missing. `package_updater.py` reports installation errors rather than
  silently continuing.
- Keep `photo_sorter.py`, `package_updater.py`, and `requirements.txt` in the
  same project folder.
- If Python reports that Tkinter is unavailable, install the Tk/Tcl component
  matching your Python distribution and version.
