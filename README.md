# Photo Sorter

The app opens with a setup window. Choose the source folder to scan, choose
one parent folder for destinations, then enter destination folder names to
create inside it. The destination folders are created when you click
**Start reviewing**. Existing folders under the selected root appear
automatically in the destination list as review choices. Enter a folder name
manually to add a destination; the app indicates whether it already exists or
will be created. Use **Exit** to close the setup window. Photos in the source
folder and its subfolders are processed one at a time. Choose a destination to
move a photo, or use **Skip photo** to leave it where it is. If a destination
already has a file with the same name,
the app adds a number to the new filename instead of overwriting it. Every
move is checked to confirm the photo is gone from the source and present in
the destination before review advances. Use **Stop review** to end early;
photos already moved stay in their destination folders. Use **Back to folder
setup** to return to the first window with your folder choices preserved.
In the review window, destination choices are large, capitalized buttons
without number prefixes. They line up in responsive columns and reflow as the
window is resized. **Skip photo**, **Exit**, and **Return to folders** are
arranged horizontally. Drag destination folder buttons in the setup list to
change the review-button order.
Each destination row also has an **Auto** checkbox and a file-type menu.
Enable it and choose a supported type to automatically move matching photos
into that folder. Each photo is still previewed individually, followed by a
brief “Moved to” notice before the next photo. JPEG and TIFF options include
both common filename extensions; each type can be assigned to only one folder.
The setup list uses compact, readable folder buttons with a clear outline on
the selected folder. Its scrollbar appears only when the list is taller than
the available area; use the mouse wheel while the pointer is over the list, or
press and drag the middle mouse button there, to scroll.

See [INSTALLATION.md](INSTALLATION.md) for setup instructions for Windows,
macOS, and Linux. The app checks and installs packages listed in
`requirements.txt` on startup using the Python interpreter that launched it.
You can also run `package_updater.py` directly to check/install them manually.

HEIC/HEIF photos are supported through `pillow-heif`, included in the
requirements.
