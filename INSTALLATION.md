# Installation guide

Image Sorter supports Windows, macOS, and Linux. Use Python 3.10 or later.
Install Python and its Tkinter GUI support, then create a virtual environment
in the Image Sorter project folder. The app checks and installs its image
packages at startup; you can also run the updater yourself.

## Windows

1. Install Python 3.10 or later from [python.org](https://www.python.org/downloads/).
   Tkinter is included with the standard Windows installer.
2. Open PowerShell and change to the folder containing `image_sorter.py`,
   `requirements.txt`, and this guide:

   ```powershell
   cd "C:\path\to\image-sorter"
   ```

3. Create the environment, install/check packages, and launch:

   ```powershell
   py -3 -m venv venv_imagesorter
   .\venv_imagesorter\Scripts\python.exe -m pip install -r requirements.txt
   .\Run Image Sorter.bat
   ```

If `py` is unavailable, use `python -m venv venv_imagesorter` if Python is on
your PATH.
After setup, double-click **Run Image Sorter.bat** to update packages and open
the GUI.

## macOS

1. Install Python 3.10 or later. The official python.org installer includes
   Tkinter. If you use another Python distribution, make sure it includes
   Tcl/Tk support.
2. Open Terminal and change to the Image Sorter project folder:

   ```sh
   cd /path/to/image-sorter
   ```

3. Create the environment, install/check packages, and launch:

   ```sh
   python3 -m venv venv_imagesorter
   ./venv_imagesorter/bin/python -m pip install -r requirements.txt
   chmod +x run_image_sorter.sh
   ./run_image_sorter.sh
   ```

After setup, double-click `run_image_sorter.sh` from a file manager configured
to run executable text files. Otherwise launch it from Terminal with
`./run_image_sorter.sh`.

## macOS app

After creating the sibling `venv_imagesorter` environment as shown above,
build the double-clickable app:

```sh
./build_macos_app.sh
```

Then double-click **Image Sorter.app** in the project folder. The app runs the
package updater before opening the GUI. If the project is moved, rebuild the
app from its new location.

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

2. Open a terminal and change to the Image Sorter project folder:

   ```sh
   cd /path/to/image-sorter
   ```

3. Create the environment, install/check packages, and launch:

   ```sh
   python3 -m venv venv_imagesorter
   ./venv_imagesorter/bin/python -m pip install -r requirements.txt
   chmod +x run_image_sorter.sh
   ./run_image_sorter.sh
   ```

After setup, double-click `run_image_sorter.sh` from a file manager configured
to run executable text files. Otherwise launch it from a terminal.

## Notes

- The first package check needs an internet connection if dependencies are
  missing. `package_updater.py` reports installation errors rather than
  silently continuing.
- Keep the launchers, `run_image_sorter.py`, `image_sorter.py`,
  `package_updater.py`, `requirements.txt`, and
  `macos_launcher.applescript` in the same project folder.
- If Python reports that Tkinter is unavailable, install the Tk/Tcl component
  matching your Python distribution and version.
