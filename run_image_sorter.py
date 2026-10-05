#!/usr/bin/env python3
"""Update Image Sorter packages, then launch the graphical app."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

from package_updater import PackageUpdateError, ensure_packages


def main() -> int:
    try:
        ensure_packages()
    except (PackageUpdateError, OSError) as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Image Sorter setup failed", str(error), parent=root)
        root.destroy()
        return 1

    from image_sorter import main as run_image_sorter

    return run_image_sorter(update_packages=False)


if __name__ == "__main__":
    sys.exit(main())
