#!/usr/bin/env python3
"""Review photos and move each one into a destination folder."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from package_updater import PackageUpdateError, ensure_packages


def load_photo_packages() -> None:
    global Image, ImageOps, ImageTk
    from PIL import Image as PillowImage
    from PIL import ImageOps as PillowImageOps
    from PIL import ImageTk as PillowImageTk
    from pillow_heif import register_heif_opener

    Image = PillowImage
    ImageOps = PillowImageOps
    ImageTk = PillowImageTk
    register_heif_opener()


PHOTO_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

AUTO_TYPE_CHOICES = {
    "AVIF": {".avif"},
    "BMP": {".bmp"},
    "GIF": {".gif"},
    "HEIC": {".heic"},
    "HEIF": {".heif"},
    "JPEG": {".jpeg", ".jpg"},
    "PNG": {".png"},
    "TIFF": {".tif", ".tiff"},
    "WebP": {".webp"},
}
AUTO_TYPE_OPTIONS = ("Choose type…", *AUTO_TYPE_CHOICES)

DESTINATION_ROW_STEP = 40

COLORS = {
    "background": "#F3F6FA",
    "surface": "#FFFFFF",
    "text": "#172B4D",
    "primary": "#1769AA",
    "primary_active": "#0F548B",
    "dragged": "#DCEBFA",
    "danger": "#A93232",
    "preview": "#17212F",
}


def configure_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    root.configure(background=COLORS["background"])
    style.configure("App.TFrame", background=COLORS["background"])
    style.configure(
        "App.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("TkDefaultFont", 12),
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("TkDefaultFont", 22, "bold"),
    )
    style.configure(
        "Section.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("TkDefaultFont", 14, "bold"),
    )
    style.configure(
        "Primary.TButton",
        font=("TkDefaultFont", 12, "bold"),
        padding=(16, 12),
        background=COLORS["primary"],
        foreground="white",
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", COLORS["primary_active"]),
            ("pressed", COLORS["primary_active"]),
        ],
    )
    style.configure("Secondary.TButton", font=("TkDefaultFont", 12), padding=(12, 9))
    style.configure("Browse.TButton", font=("TkDefaultFont", 11), padding=(10, 6))
    style.configure(
        "Stop.TButton",
        font=("TkDefaultFont", 12, "bold"),
        padding=(14, 10),
        background=COLORS["danger"],
        foreground="white",
    )
    style.map("Stop.TButton", background=[("active", "#872828")])
    style.configure("App.TEntry", font=("TkDefaultFont", 13), padding=9)


def set_drag_cursor(widget: tk.Widget, dragging: bool = True) -> None:
    if not dragging:
        widget.configure(cursor="")
        return
    try:
        widget.configure(cursor="closedhand")
    except tk.TclError:
        widget.configure(cursor="hand2")


def destination_column_count(available_width: int, destination_count: int) -> int:
    """Choose a readable number of destination buttons per row."""
    if destination_count <= 0:
        return 1
    return min(destination_count, max(1, (available_width + 12) // 240))


def unique_destination(folder: Path, filename: str) -> Path:
    """Return a destination path that will not overwrite an existing file."""
    candidate = folder / filename
    if not candidate.exists():
        return candidate

    original = Path(filename)
    number = 1
    while True:
        candidate = folder / f"{original.stem} ({number}){original.suffix}"
        if not candidate.exists():
            return candidate
        number += 1


class SetupWindow:
    def __init__(
        self,
        root: tk.Tk,
        source: Path | None = None,
        destination_root: Path | None = None,
        destinations: list[Path] | None = None,
        auto_rules: dict[Path, str] | None = None,
    ):
        self.root = root
        self.source = source
        self.destination_root = destination_root
        self.destinations = list(destinations or [])
        self.auto_rules = auto_rules or {}
        self._drag_index: int | None = None
        self._selected_destination: int | None = None
        self.destination_rows: dict[Path, ttk.Frame] = {}
        self.destination_row_buttons: dict[Path, tk.Button] = {}
        self.auto_type_vars: dict[Path, tk.StringVar] = {}
        self.auto_enabled_vars: dict[Path, tk.BooleanVar] = {}
        self._row_animation_id: str | None = None
        self._drag_preview: tk.Toplevel | None = None
        self._drag_preview_label: tk.Label | None = None
        self._drag_offset = (14, 14)
        self._middle_scroll_active = False

        root.title("Photo Sorter")
        root.geometry("900x740")
        root.minsize(680, 620)
        configure_styles(root)

        self.frame = ttk.Frame(root, padding=28, style="App.TFrame")
        self.frame.pack(fill="both", expand=True)

        ttk.Label(
            self.frame,
            text="Choose folders to get started",
            style="Title.TLabel",
        ).pack(anchor="w", pady=(0, 16))
        ttk.Label(
            self.frame,
            text="Select the folder to scan, then add one or more destination folders.",
            style="App.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        self.folder_selectors = ttk.Frame(self.frame, style="App.TFrame")
        self.folder_selectors.pack(fill="x", pady=(8, 24))
        self.folder_selectors.grid_columnconfigure(0, weight=0, minsize=220)
        self.folder_selectors.grid_columnconfigure(1, weight=1)

        self.folder_button_width = 220
        self.source_label = ttk.Label(
            self.folder_selectors,
            text=str(self.source) if self.source else "No photo folder selected",
            wraplength=360,
            style="App.TLabel",
            anchor="w",
        )
        self.source_label.grid(row=0, column=1, sticky="new", padx=(16, 0))
        self.source_button_slot = ttk.Frame(
            self.folder_selectors,
            style="App.TFrame",
        )
        self.source_button_slot.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.source_button = ttk.Button(
            self.source_button_slot,
            text="Choose photo folder…",
            command=self.choose_source,
            style="Browse.TButton",
        )
        self.source_button.pack(fill="both", expand=True)

        self.destination_root_label = ttk.Label(
            self.folder_selectors,
            text=(
                str(self.destination_root)
                if self.destination_root
                else "No destination root selected"
            ),
            wraplength=360,
            style="App.TLabel",
            anchor="w",
        )
        self.destination_root_label.grid(
            row=1, column=1, sticky="new", padx=(16, 0)
        )
        self.destination_root_button_slot = ttk.Frame(
            self.folder_selectors,
            style="App.TFrame",
        )
        self.destination_root_button_slot.grid(row=1, column=0, sticky="ew")
        self.destination_root_button = ttk.Button(
            self.destination_root_button_slot,
            text="Choose destination root…",
            command=self.choose_destination_root,
            style="Browse.TButton",
        )
        self.destination_root_button.pack(fill="both", expand=True)

        destination_name_row = ttk.Frame(self.frame, style="App.TFrame")
        destination_name_row.pack(fill="x", pady=(0, 6))
        ttk.Label(
            destination_name_row, text="New folder name:", style="App.TLabel"
        ).pack(side="left")
        self.destination_name = ttk.Entry(destination_name_row, style="App.TEntry")
        self.destination_name.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.destination_name.bind("<Return>", lambda _event: self.add_destination())
        self.destination_name.bind("<KeyRelease>", self.update_destination_status)
        ttk.Button(
            destination_name_row,
            text="Add folder",
            command=self.add_destination,
            style="Secondary.TButton",
        ).pack(side="left")
        self.destination_status = ttk.Label(
            self.frame,
            text="Choose a root folder to see existing folders.",
            style="App.TLabel",
        )
        self.destination_status.pack(anchor="w", fill="x", pady=(2, 8))

        destinations_area = ttk.Frame(self.frame, style="App.TFrame")
        destinations_area.pack(fill="both", expand=True, pady=(6, 8))
        destinations_area.grid_rowconfigure(0, weight=1)
        destinations_area.grid_columnconfigure(0, weight=1)
        self.destination_canvas = tk.Canvas(
            destinations_area,
            background=COLORS["background"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.destination_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            destinations_area,
            orient="vertical",
            command=self.destination_canvas.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar.grid_remove()
        self.destination_scrollbar = scrollbar
        self.destination_canvas.configure(yscrollcommand=scrollbar.set)
        self.destination_rows_frame = ttk.Frame(
            self.destination_canvas, style="App.TFrame"
        )
        self.destination_rows_window = self.destination_canvas.create_window(
            (0, 0), window=self.destination_rows_frame, anchor="nw"
        )
        self.destination_rows_frame.bind(
            "<Configure>",
            lambda _event: self.update_destination_scrollregion(),
        )
        self.destination_canvas.bind(
            "<Configure>",
            self.resize_destination_rows,
        )
        self.root.bind_all("<ButtonPress-2>", self.begin_middle_scroll)
        self.root.bind_all("<B2-Motion>", self.middle_scroll)
        self.root.bind_all("<ButtonRelease-2>", self.finish_middle_scroll)
        self.render_destination_rows()
        ttk.Label(
            self.frame,
            text=(
                "Drag a folder button to reorder it. Turn on Auto and choose a "
                "file type to move matching photos there without review."
            ),
            style="App.TLabel",
        ).pack(anchor="w", pady=(0, 6))

        destination_actions = ttk.Frame(self.frame)
        destination_actions.pack(fill="x")
        ttk.Button(
            destination_actions,
            text="Remove selected",
            command=self.remove_destination,
            style="Secondary.TButton",
        ).pack(side="left")

        footer = ttk.Frame(self.frame, style="App.TFrame")
        footer.pack(fill="x", pady=(18, 0))
        ttk.Button(
            footer,
            text="Exit",
            command=self.root.destroy,
            style="Secondary.TButton",
        ).pack(side="left")
        self.start_button = ttk.Button(
            footer,
            text="Start reviewing",
            command=self.start_review,
            style="Primary.TButton",
        )
        self.start_button.pack(side="right")
        root.bind("<Configure>", self.on_resize)

    def on_resize(self, _event: tk.Event) -> None:
        if _event.widget is not self.root:
            return
        window_width = self.root.winfo_width()
        available_width = max(1, window_width - 96)
        button_width = min(300, max(220, round(available_width * 0.36)))
        self.folder_button_width = button_width
        self.folder_selectors.grid_columnconfigure(0, minsize=button_width)
        self.source_button_slot.configure(width=button_width)
        self.destination_root_button_slot.configure(width=button_width)
        wraplength = max(160, available_width - button_width - 16)
        self.source_label.configure(wraplength=wraplength)
        self.destination_root_label.configure(wraplength=wraplength)

    def render_destination_rows(self, *, rebuild: bool = True) -> None:
        if rebuild and self._row_animation_id is not None:
            self.root.after_cancel(self._row_animation_id)
            self._row_animation_id = None

        if rebuild:
            for row in self.destination_rows.values():
                row.destroy()
            self.destination_rows.clear()
            self.destination_row_buttons.clear()

        for index, destination in enumerate(self.destinations):
            selected = index == self._selected_destination
            row = self.destination_rows.get(destination)
            if row is None:
                row = ttk.Frame(self.destination_rows_frame, style="App.TFrame")
                row.grid_columnconfigure(0, weight=1)
                button = tk.Button(
                    row,
                    text=f"↕  {destination.name}",
                    anchor="w",
                    font=("TkDefaultFont", 11, "bold"),
                    activebackground=COLORS["primary_active"],
                    activeforeground="white",
                    relief="raised",
                    borderwidth=1,
                    highlightthickness=0,
                    highlightbackground=COLORS["primary"],
                    highlightcolor=COLORS["primary"],
                    padx=10,
                    pady=4,
                    cursor="hand2",
                )
                button.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
                button.bind(
                    "<ButtonPress-1>",
                    lambda event, item=destination: self.begin_destination_drag(
                        item, event
                    ),
                )
                type_var = self.auto_type_vars.get(destination)
                if type_var is None:
                    type_var = tk.StringVar(
                        value=self.auto_rules.get(destination, AUTO_TYPE_OPTIONS[0])
                    )
                enabled_var = self.auto_enabled_vars.get(destination)
                if enabled_var is None:
                    enabled_var = tk.BooleanVar(
                        value=destination in self.auto_rules
                    )
                ttk.Checkbutton(
                    row,
                    text="Auto",
                    variable=enabled_var,
                ).grid(row=0, column=1, padx=(0, 8))
                ttk.Combobox(
                    row,
                    textvariable=type_var,
                    values=AUTO_TYPE_OPTIONS,
                    state="readonly",
                    width=12,
                ).grid(row=0, column=2, sticky="e")
                self.destination_rows[destination] = row
                self.destination_row_buttons[destination] = button
                self.auto_type_vars[destination] = type_var
                self.auto_enabled_vars[destination] = enabled_var
            button = self.destination_row_buttons[destination]
            button.configure(
                text=f"↕  {destination.name}",
                background=COLORS["dragged"] if selected else COLORS["surface"],
                foreground=COLORS["text"],
                relief="solid" if selected else "raised",
                borderwidth=2 if selected else 1,
                highlightthickness=3 if selected else 0,
            )

        for destination in tuple(self.destination_rows):
            if destination not in self.destinations:
                self.destination_rows.pop(destination).destroy()
                self.destination_row_buttons.pop(destination)
                self.auto_type_vars.pop(destination)
                self.auto_enabled_vars.pop(destination)

        if rebuild:
            self.layout_destination_rows()

    def resize_destination_rows(self, event: tk.Event) -> None:
        self.destination_canvas.itemconfigure(
            self.destination_rows_window, width=event.width
        )
        self.layout_destination_rows()
        self.update_destination_scrollregion()

    def update_destination_scrollregion(self) -> None:
        bounds = self.destination_canvas.bbox("all")
        if bounds is None:
            self.destination_canvas.configure(scrollregion=(0, 0, 0, 0))
            self.destination_scrollbar.grid_remove()
            return

        self.destination_canvas.configure(scrollregion=bounds)
        content_height = bounds[3] - bounds[1]
        viewport_height = self.destination_canvas.winfo_height()
        if content_height > viewport_height:
            self.destination_scrollbar.grid()
        else:
            self.destination_scrollbar.grid_remove()
            self.destination_canvas.yview_moveto(0)

    def pointer_is_over_destination_list(self, event: tk.Event) -> bool:
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        while widget is not None:
            if widget == self.destination_canvas:
                return True
            widget = getattr(widget, "master", None)
        return False

    def begin_middle_scroll(self, event: tk.Event) -> None:
        if not self.pointer_is_over_destination_list(event):
            return
        self._middle_scroll_active = True
        self.destination_canvas.scan_mark(
            event.x_root - self.destination_canvas.winfo_rootx(),
            event.y_root - self.destination_canvas.winfo_rooty(),
        )

    def middle_scroll(self, event: tk.Event) -> None:
        if not self._middle_scroll_active:
            return
        self.destination_canvas.scan_dragto(
            event.x_root - self.destination_canvas.winfo_rootx(),
            event.y_root - self.destination_canvas.winfo_rooty(),
            gain=1,
        )

    def finish_middle_scroll(self, _event: tk.Event) -> None:
        self._middle_scroll_active = False

    def destination_mousewheel(self, event: tk.Event) -> str | None:
        if not self.pointer_is_over_destination_list(event):
            return None

        event_number = getattr(event, "num", None)
        if event_number == 4:
            units = -1
        elif event_number == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return "break"
            steps = max(1, round(abs(delta) / 120))
            units = -steps if delta > 0 else steps

        self.destination_canvas.yview_scroll(units, "units")
        return "break"

    def layout_destination_rows(self) -> None:
        canvas_width = max(1, self.destination_canvas.winfo_width())
        content_height = max(
            DESTINATION_ROW_STEP,
            len(self.destinations) * DESTINATION_ROW_STEP,
        )
        self.destination_rows_frame.configure(
            width=canvas_width,
            height=content_height,
        )
        self.destination_canvas.configure(
            scrollregion=(0, 0, canvas_width, content_height)
        )
        for index, destination in enumerate(self.destinations):
            self.destination_rows[destination].place_configure(
                x=3,
                y=index * DESTINATION_ROW_STEP + 3,
                width=max(1, canvas_width - 6),
                height=DESTINATION_ROW_STEP - 6,
            )

    def select_destination(self, index: int) -> None:
        self._selected_destination = index
        self.render_destination_rows()

    def begin_destination_drag(self, destination: Path, event: tk.Event) -> str:
        index = self.destinations.index(destination)
        self._drag_index = index
        self._selected_destination = index
        self.root.bind_all("<B1-Motion>", self.drag_destination)
        self.root.bind_all("<ButtonRelease-1>", self.finish_destination_drag)
        self.render_destination_rows(rebuild=False)
        set_drag_cursor(self.root)
        self.show_drag_preview(destination, event.x_root, event.y_root)
        return "break"

    def drag_destination(self, event: tk.Event) -> str:
        if self._drag_index is None or not self.destinations:
            return "break"

        self.move_drag_preview(event.x_root, event.y_root)
        local_y = self.destination_canvas.canvasy(
            event.y_root - self.destination_canvas.winfo_rooty()
        )
        target = min(
            len(self.destinations) - 1,
            max(0, int(local_y // DESTINATION_ROW_STEP)),
        )
        if target != self._drag_index:
            if self._row_animation_id is not None:
                self.root.after_cancel(self._row_animation_id)
                self._row_animation_id = None
            starts = {
                destination: row.winfo_y()
                for destination, row in self.destination_rows.items()
            }
            destination = self.destinations.pop(self._drag_index)
            self.destinations.insert(target, destination)
            self._drag_index = target
            self._selected_destination = target
            self.render_destination_rows(rebuild=False)
            self.animate_destination_rows(starts)
        return "break"

    def animate_destination_rows(self, starts: dict[Path, int]) -> None:
        ends = {
            destination: index * DESTINATION_ROW_STEP + 3
            for index, destination in enumerate(self.destinations)
        }
        frames = 12

        def animate(frame: int) -> None:
            fraction = frame / frames
            eased = 1 - (1 - fraction) ** 3
            for destination, row in self.destination_rows.items():
                start = starts.get(destination, ends[destination])
                end = ends[destination]
                row.place_configure(y=round(start + (end - start) * eased))
            if frame < frames:
                self._row_animation_id = self.root.after(
                    14, lambda: animate(frame + 1)
                )
            else:
                self._row_animation_id = None
                self.layout_destination_rows()

        animate(1)

    def show_drag_preview(self, destination: Path, x: int, y: int) -> None:
        self.hide_drag_preview()
        preview = tk.Toplevel(self.root)
        preview.overrideredirect(True)
        try:
            preview.attributes("-alpha", 0.88)
        except tk.TclError:
            pass
        label = tk.Label(
            preview,
            text=f"↕  {destination.name}",
            anchor="w",
            font=("TkDefaultFont", 13, "bold"),
            background=COLORS["dragged"],
            foreground=COLORS["text"],
            padx=14,
            pady=10,
            relief="raised",
            borderwidth=1,
        )
        label.pack(fill="both", expand=True)
        self._drag_preview = preview
        self._drag_preview_label = label
        self.move_drag_preview(x, y)

    def move_drag_preview(self, x: int, y: int) -> None:
        if self._drag_preview is not None:
            offset_x, offset_y = self._drag_offset
            self._drag_preview.geometry(f"+{x + offset_x}+{y + offset_y}")

    def hide_drag_preview(self) -> None:
        if self._drag_preview is not None:
            self._drag_preview.destroy()
            self._drag_preview = None
            self._drag_preview_label = None

    def finish_destination_drag(self, _event: tk.Event) -> str:
        self.root.unbind_all("<B1-Motion>")
        self.root.unbind_all("<ButtonRelease-1>")
        self._drag_index = None
        self.hide_drag_preview()
        set_drag_cursor(self.root, dragging=False)
        return "break"

    def choose_source(self) -> None:
        selected = filedialog.askdirectory(
            parent=self.root, title="Choose the folder containing the photos"
        )
        if selected:
            self.source = Path(selected).resolve()
            self.source_label.configure(text=str(self.source))

    def choose_destination_root(self) -> None:
        selected = filedialog.askdirectory(
            parent=self.root, title="Choose the parent folder for destinations"
        )
        if selected:
            new_root = Path(selected).resolve()
            try:
                existing_folders = sorted(
                    (
                        path.name
                        for path in new_root.iterdir()
                        if path.is_dir() and not path.is_symlink()
                    ),
                    key=str.casefold,
                )
            except OSError as error:
                messagebox.showerror(
                    "Could not check destination root",
                    f"{new_root}\n\n{error}",
                    parent=self.root,
                )
                return
            destination_names = set(existing_folders)
            destination_names.update(
                destination.name for destination in self.destinations
            )
            new_destinations = [
                (new_root / name).resolve()
                for name in sorted(destination_names, key=str.casefold)
            ]
            if self.source and any(
                destination == self.source or self.source in destination.parents
                for destination in new_destinations
            ):
                messagebox.showerror(
                    "Invalid destination root",
                    "That root would put a destination inside the photo folder.",
                    parent=self.root,
                )
                return

            self.destination_root = new_root
            self.destination_root_label.configure(text=str(self.destination_root))
            self.destinations = new_destinations
            self._selected_destination = None
            self.render_destination_rows()
            self.update_destination_status()

    def update_destination_status(self, _event: tk.Event | None = None) -> None:
        folder_name = self.destination_name.get().strip()
        if self.destination_root is None:
            self.destination_status.configure(
                text="Choose a root folder to see existing folders."
            )
            return
        if (
            not folder_name
            or folder_name in {".", ".."}
            or Path(folder_name).name != folder_name
        ):
            self.destination_status.configure(
                text="Choose an existing folder or enter a new folder name."
            )
            return

        destination = self.destination_root / folder_name
        if destination.is_dir():
            status = "Existing folder — it will be used."
        elif destination.exists():
            status = "That name already exists, but it is not a folder."
        else:
            status = "New folder — it will be created when you start."
        self.destination_status.configure(text=status)

    def add_destination(self) -> None:
        if self.destination_root is None:
            messagebox.showerror(
                "Choose a destination root",
                "Select the parent folder where your destination folders will be created.",
                parent=self.root,
            )
            return

        folder_name = self.destination_name.get().strip()
        if (
            not folder_name
            or folder_name in {".", ".."}
            or Path(folder_name).name != folder_name
        ):
            messagebox.showerror(
                "Invalid folder name",
                "Enter a single folder name, without a path.",
                parent=self.root,
            )
            return

        destination = (self.destination_root / folder_name).resolve()
        if destination.exists() and not destination.is_dir():
            messagebox.showerror(
                "Not a folder",
                f"A file with that name already exists:\n{destination}",
                parent=self.root,
            )
            return
        if destination in self.destinations:
            return
        if self.source and (
            destination == self.source or self.source in destination.parents
        ):
            messagebox.showerror(
                "Invalid destination",
                "A destination cannot be the source folder or a folder inside it.",
                parent=self.root,
            )
            return

        self.destinations.append(destination)
        self._selected_destination = len(self.destinations) - 1
        self.render_destination_rows()
        self.destination_name.delete(0, tk.END)
        self.update_destination_status()

    def remove_destination(self) -> None:
        if self._selected_destination is None:
            return
        destination = self.destinations.pop(self._selected_destination)
        self.auto_rules.pop(destination, None)
        self._selected_destination = None
        self.render_destination_rows()

    def start_review(self) -> None:
        if self.source is None:
            messagebox.showerror(
                "Choose a photo folder",
                "Select the folder you want Photo Sorter to scan.",
                parent=self.root,
            )
            return
        if not self.destinations:
            messagebox.showerror(
                "Add a destination",
                "Choose a destination root and add at least one destination folder.",
                parent=self.root,
            )
            return
        if any(
            destination == self.source or self.source in destination.parents
            for destination in self.destinations
        ):
            messagebox.showerror(
                "Invalid destination",
                "A destination cannot be the source folder or a folder inside it.",
                parent=self.root,
            )
            return

        auto_rules: dict[Path, str] = {}
        used_extensions: dict[str, Path] = {}
        for destination in self.destinations:
            if not self.auto_enabled_vars[destination].get():
                continue
            type_name = self.auto_type_vars[destination].get()
            if type_name not in AUTO_TYPE_CHOICES:
                messagebox.showerror(
                    "Choose an automatic file type",
                    f"Choose a file type for the automatic rule on "
                    f"{destination.name}.",
                    parent=self.root,
                )
                return
            for extension in AUTO_TYPE_CHOICES[type_name]:
                if extension in used_extensions:
                    messagebox.showerror(
                        "Duplicate automatic file type",
                        f"{extension.upper()} is assigned to both "
                        f"{used_extensions[extension].name} and "
                        f"{destination.name}. Assign each type to only one folder.",
                        parent=self.root,
                    )
                    return
                used_extensions[extension] = destination
            auto_rules[destination] = type_name

        try:
            destinations = [destination.resolve() for destination in self.destinations]
            if any(
                destination == self.source or self.source in destination.parents
                for destination in destinations
            ):
                messagebox.showerror(
                    "Invalid destination",
                    "A destination cannot be the source folder or a folder inside it.",
                    parent=self.root,
                )
                return
            for destination in destinations:
                destination.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror(
                "Could not create destination folders",
                str(error),
                parent=self.root,
            )
            return

        self.frame.destroy()
        PhotoSorter(self.root, self.source, destinations, auto_rules)


class PhotoSorter:
    def __init__(
        self,
        root: tk.Tk,
        source: Path,
        destinations: list[Path],
        auto_rules: dict[Path, str] | None = None,
    ):
        self.root = root
        self.source = source
        self.destinations = destinations
        self.auto_rules = auto_rules or {}
        self.auto_destinations = {
            extension: destination
            for destination, type_name in self.auto_rules.items()
            for extension in AUTO_TYPE_CHOICES[type_name]
        }
        self.photos = sorted(
            (
                path
                for path in source.rglob("*")
                if path.is_file() and path.suffix.lower() in PHOTO_EXTENSIONS
            ),
            key=lambda path: str(path).casefold(),
        )
        self.index = 0
        self.original_image: Image.Image | None = None
        self.photo_image: ImageTk.PhotoImage | None = None
        self.image_error = False
        self._resize_job: str | None = None
        self._destination_columns = 0
        self._auto_move_pending = False
        self._auto_move_job: str | None = None
        self._auto_advance_job: str | None = None
        self._auto_failed_paths: set[Path] = set()

        root.title("Photo Sorter")
        root.geometry("1100x850")
        root.minsize(760, 620)
        configure_styles(root)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.bind("<Configure>", self.on_resize)

        self.status = ttk.Label(root, anchor="center", style="Title.TLabel")
        self.status.pack(fill="x", padx=24, pady=(20, 8))

        self.preview_frame = tk.Frame(root, background=COLORS["preview"])
        self.preview_frame.pack(fill="both", expand=True, padx=24, pady=10)
        self.preview = tk.Label(
            self.preview_frame,
            text="",
            background=COLORS["preview"],
            foreground="white",
            anchor="center",
        )
        self.preview.pack(fill="both", expand=True)
        self.auto_move_notice = tk.Label(
            self.preview_frame,
            text="",
            background="#DDF3E4",
            foreground="#174B2A",
            font=("TkDefaultFont", 10, "bold"),
            padx=9,
            pady=5,
        )

        self.filename = ttk.Label(root, anchor="center", style="App.TLabel")
        self.filename.pack(fill="x", padx=24, pady=8)

        self.buttons = ttk.Frame(root, style="App.TFrame")
        self.buttons.pack(fill="x", padx=24, pady=(4, 8))
        self.destination_buttons: list[tk.Button] = []
        for number, destination in enumerate(destinations, start=1):
            label = (destination.name or str(destination)).upper()
            button = tk.Button(
                self.buttons,
                text=label,
                command=lambda folder=destination: self.move_current(folder),
                font=("TkDefaultFont", 15, "bold"),
                background=COLORS["primary"],
                foreground=COLORS["text"],
                activebackground=COLORS["primary_active"],
                activeforeground=COLORS["text"],
                disabledforeground="#52647A",
                relief="flat",
                borderwidth=0,
                padx=16,
                pady=14,
                justify="center",
                wraplength=220,
                cursor="hand2",
            )
            self.destination_buttons.append(button)
            if number <= 9:
                root.bind(
                    f"<KeyPress-{number}>",
                    lambda _event, folder=destination: self.move_current(folder),
                )
        self.layout_destination_buttons()
        self.buttons.bind(
            "<Configure>", lambda _event: self.layout_destination_buttons()
        )

        self.review_controls = ttk.Frame(root, style="App.TFrame")
        self.review_controls.pack(fill="x", padx=24, pady=(4, 18))
        for column in range(3):
            self.review_controls.grid_columnconfigure(
                column, weight=1, uniform="controls"
            )
        self.skip_button = ttk.Button(
            self.review_controls,
            text="Skip photo",
            command=self.skip_current,
            style="Secondary.TButton",
        )
        self.skip_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            self.review_controls,
            text="Exit",
            command=self.stop_review,
            style="Stop.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(
            self.review_controls,
            text="Return to folders",
            command=self.return_to_setup,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        if not self.photos:
            messagebox.showinfo(
                "Photo Sorter",
                "No supported photo files were found in that folder or its subfolders.",
                parent=root,
            )
            root.destroy()
        else:
            self.show_current()

    def on_resize(self, _event: tk.Event) -> None:
        if _event.widget is not self.root:
            return
        if not self.preview.winfo_exists():
            return
        if self.original_image is not None:
            self.render_image()
        if self._resize_job is not None:
            try:
                self.root.after_cancel(self._resize_job)
            except tk.TclError:
                self._resize_job = None
                return
        self._resize_job = self.root.after_idle(self.layout_destination_buttons)

    def layout_destination_buttons(self) -> None:
        self._resize_job = None
        if not self.destination_buttons:
            return

        available_width = max(1, self.buttons.winfo_width())
        columns = destination_column_count(
            available_width, len(self.destination_buttons)
        )
        if columns != self._destination_columns:
            for button in self.destination_buttons:
                button.grid_forget()
            for column in range(max(columns, self._destination_columns)):
                self.buttons.grid_columnconfigure(column, weight=0, uniform="")
            for column in range(columns):
                self.buttons.grid_columnconfigure(column, weight=1, uniform="destinations")
            for index, button in enumerate(self.destination_buttons):
                button.grid(
                    row=index // columns,
                    column=index % columns,
                    sticky="nsew",
                    padx=6,
                    pady=5,
                )
            self._destination_columns = columns

        button_width = max(1, available_width // columns)
        for button in self.destination_buttons:
            button.configure(wraplength=max(140, button_width - 48))

    def render_image(self) -> None:
        if self.original_image is None or not self.preview.winfo_exists():
            return
        width = max(1, self.preview.winfo_width() - 16)
        height = max(1, self.preview.winfo_height() - 16)
        image = self.original_image.copy()
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(image)
        self.preview.configure(image=self.photo_image, text="")

    def show_current(self) -> None:
        if self.index >= len(self.photos):
            messagebox.showinfo(
                "Photo Sorter", "You have reviewed all the photos.", parent=self.root
            )
            self.root.destroy()
            return

        path = self.photos[self.index]
        self.status.configure(text=f"Photo {self.index + 1} of {len(self.photos)}")
        self.filename.configure(text=str(path.relative_to(self.source)))
        self.original_image = None
        self.image_error = False
        self.photo_image = None
        self.auto_move_notice.place_forget()

        try:
            with Image.open(path) as image:
                self.original_image = ImageOps.exif_transpose(image).copy()
        except (OSError, ValueError) as error:
            self.image_error = True
            self.preview.configure(
                image="",
                text=f"Unable to display this photo:\n{error}",
                wraplength=700,
            )
        else:
            self.render_image()

        for button in self.destination_buttons:
            button.configure(state="disabled" if self.image_error else "normal")
        self.skip_button.configure(state="normal")

        if (
            not self.image_error
            and path not in self._auto_failed_paths
            and path.suffix.lower() in self.auto_destinations
        ):
            self._auto_move_pending = True
            for button in self.destination_buttons:
                button.configure(state="disabled")
            self.skip_button.configure(state="disabled")
            self._auto_move_job = self.root.after(
                100, lambda current=path: self.move_current_automatically(current)
            )

    def move_current_automatically(self, path: Path) -> None:
        self._auto_move_job = None
        if not self._auto_move_pending or self.index >= len(self.photos):
            return
        if self.photos[self.index] != path:
            self._auto_move_pending = False
            return

        destination = self.auto_destinations[path.suffix.lower()]
        try:
            self.move_photo_file(path, destination)
        except OSError as error:
            self._auto_move_pending = False
            self._auto_failed_paths.add(path)
            messagebox.showerror(
                "Could not automatically move photo",
                f"{path.name}\n\n{error}\n\n"
                "The photo will remain available for manual review.",
                parent=self.root,
            )
            for button in self.destination_buttons:
                button.configure(state="disabled" if self.image_error else "normal")
            self.skip_button.configure(state="normal")
            return

        self.auto_move_notice.configure(text=f"Moved to {destination.name}")
        self.auto_move_notice.place(relx=1, rely=1, anchor="se", x=-12, y=-12)
        self._auto_advance_job = self.root.after(
            500, self.advance_after_automatic_move
        )

    def advance_after_automatic_move(self) -> None:
        self._auto_advance_job = None
        self.index += 1
        self._auto_move_pending = False
        self.show_current()

    def move_current(self, destination: Path) -> None:
        if (
            self._auto_move_pending
            or self.image_error
            or self.index >= len(self.photos)
        ):
            return
        path = self.photos[self.index]
        try:
            self.move_photo_file(path, destination)
        except OSError as error:
            messagebox.showerror(
                "Could not move photo",
                f"{path.name}\n\n{error}",
                parent=self.root,
            )
            return
        self.index += 1
        self.show_current()

    @staticmethod
    def move_photo_file(path: Path, destination: Path) -> None:
        target = unique_destination(destination, path.name)
        shutil.move(str(path), str(target))
        if path.exists():
            raise OSError(
                "The move operation finished, but the original still exists "
                "in the source folder. It was not marked as complete."
            )
        if not target.is_file():
            raise OSError(
                f"The photo is no longer in the source, but the destination "
                f"file was not found at {target}."
            )

    def skip_current(self) -> None:
        if self._auto_move_pending:
            return
        self.index += 1
        self.show_current()

    def stop_review(self) -> None:
        if messagebox.askyesno(
            "Stop reviewing?",
            "Stop reviewing the remaining photos now?\n\n"
            "Photos already moved will stay in their destination folders.",
            parent=self.root,
        ):
            self.root.destroy()

    def return_to_setup(self) -> None:
        for job in (self._auto_move_job, self._auto_advance_job):
            if job is not None:
                self.root.after_cancel(job)
        self._auto_move_job = None
        self._auto_advance_job = None
        self._auto_move_pending = False
        for number in range(1, 10):
            self.root.unbind(f"<KeyPress-{number}>")
        for child in self.root.winfo_children():
            child.destroy()
        SetupWindow(
            self.root,
            source=self.source,
            destination_root=self.destinations[0].parent if self.destinations else None,
            destinations=self.destinations,
            auto_rules=self.auto_rules,
        )


def main() -> int:
    try:
        ensure_packages()
        load_photo_packages()
    except (PackageUpdateError, ImportError, OSError) as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Photo Sorter setup failed", str(error), parent=root)
        root.destroy()
        return 1

    root = tk.Tk()
    configure_styles(root)
    SetupWindow(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
