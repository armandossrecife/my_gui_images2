import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import PIL.Image
import PIL.ImageTk

from .constants import COLORS, FONT_FAMILY, THUMBNAIL_SIZE
from .helpers import calculate_grid_columns


class GalleryPanel(ttk.Frame):
    def __init__(self, parent, on_select):
        super().__init__(parent, style="Surface.TFrame", padding=(18, 18, 10, 12))
        self.on_select = on_select
        self.image_paths = []
        self.selected_path = None
        self.thumbnail_photos = {}
        self.card_frames = {}
        self._columns = 0
        self._reflow_job = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_widgets()

    def _build_widgets(self):
        header = ttk.Frame(self, style="Surface.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=(2, 8), pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Biblioteca", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.count_label = ttk.Label(header, text="0 imagens", style="Badge.TLabel")
        self.count_label.grid(row=0, column=1, sticky="e")

        canvas_frame = ttk.Frame(self, style="Surface.TFrame")
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_frame,
            background=COLORS["surface"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            style="App.Vertical.TScrollbar",
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = tk.Frame(self.canvas, background=COLORS["surface"])
        self.canvas_window = self.canvas.create_window(
            (0, 0), anchor="nw", window=self.inner_frame
        )
        self.inner_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._schedule_reflow)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def set_images(self, image_paths, selected_path=None):
        self.image_paths = [os.fspath(path) for path in image_paths]
        self.selected_path = os.fspath(selected_path) if selected_path else None
        count = len(self.image_paths)
        self.count_label.configure(
            text=f"{count} {'imagem' if count == 1 else 'imagens'}"
        )
        self._columns = 0
        self._render_cards(force=True)

    def select_path(self, image_path, notify=True):
        image_path = os.fspath(image_path)
        if image_path not in self.image_paths:
            return
        previous = self.selected_path
        self.selected_path = image_path
        self._update_card_appearance(previous)
        self._update_card_appearance(self.selected_path)
        if notify:
            self.on_select(image_path)

    def _schedule_reflow(self, event=None):
        width = event.width if event else self.canvas.winfo_width()
        self.canvas.itemconfigure(self.canvas_window, width=max(width, 1))
        if self._reflow_job:
            self.after_cancel(self._reflow_job)
        self._reflow_job = self.after(80, self._render_cards)

    def _render_cards(self, force=False):
        self._reflow_job = None
        columns = calculate_grid_columns(self.canvas.winfo_width())
        if not force and columns == self._columns:
            return
        self._columns = columns

        for child in self.inner_frame.winfo_children():
            child.destroy()
        self.card_frames.clear()

        for column in range(columns):
            self.inner_frame.grid_columnconfigure(column, weight=1, uniform="gallery")

        if not self.image_paths:
            empty = tk.Frame(
                self.inner_frame,
                background=COLORS["surface_muted"],
                padx=24,
                pady=34,
            )
            empty.grid(row=0, column=0, columnspan=columns, sticky="ew", padx=4, pady=4)
            tk.Label(
                empty,
                text="Sua biblioteca está vazia",
                background=COLORS["surface_muted"],
                foreground=COLORS["text"],
                font=(FONT_FAMILY, 13, "bold"),
            ).pack()
            tk.Label(
                empty,
                text="Baixe uma imagem usando o campo acima.",
                background=COLORS["surface_muted"],
                foreground=COLORS["text_muted"],
                font=(FONT_FAMILY, 10),
            ).pack(pady=(6, 0))
            self._update_scroll_region()
            return

        for index, image_path in enumerate(reversed(self.image_paths)):
            row, column = divmod(index, columns)
            card = self._create_card(image_path)
            card.grid(row=row, column=column, sticky="n", padx=5, pady=5)

        self._update_scroll_region()

    def _create_card(self, image_path):
        is_selected = image_path == self.selected_path
        border_color = COLORS["primary"] if is_selected else COLORS["border"]
        card = tk.Frame(
            self.inner_frame,
            background=COLORS["surface"],
            highlightbackground=border_color,
            highlightcolor=border_color,
            highlightthickness=2 if is_selected else 1,
            width=164,
            height=164,
            cursor="hand2",
        )
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)
        self.card_frames[image_path] = card

        photo, dimensions = self._load_thumbnail(image_path)
        image_label = tk.Label(
            card,
            image=photo,
            background=COLORS["surface_muted"],
            borderwidth=0,
            cursor="hand2",
        )
        image_label.grid(row=0, column=0, sticky="nsew", padx=7, pady=(7, 5))

        name = Path(image_path).name
        display_name = name if len(name) <= 22 else f"{name[:19]}…"
        name_label = tk.Label(
            card,
            text=display_name,
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=(FONT_FAMILY, 10, "bold"),
            anchor="w",
        )
        name_label.grid(row=1, column=0, sticky="ew", padx=8)

        dimensions_label = tk.Label(
            card,
            text=dimensions,
            background=COLORS["surface"],
            foreground=COLORS["text_muted"],
            font=(FONT_FAMILY, 9),
            anchor="w",
        )
        dimensions_label.grid(row=2, column=0, sticky="ew", padx=8, pady=(2, 7))

        for widget in (card, image_label, name_label, dimensions_label):
            widget.bind(
                "<Button-1>",
                lambda _event, path=image_path: self.select_path(path),
            )
            widget.bind(
                "<Return>",
                lambda _event, path=image_path: self.select_path(path),
            )
        card.configure(takefocus=True)
        return card

    def _load_thumbnail(self, image_path):
        cached = self.thumbnail_photos.get(image_path)
        if cached:
            return cached

        try:
            with PIL.Image.open(image_path) as image:
                width, height = image.size
                thumbnail = image.convert("RGBA")
                thumbnail.thumbnail(THUMBNAIL_SIZE, PIL.Image.Resampling.LANCZOS)
                plate = PIL.Image.new("RGBA", THUMBNAIL_SIZE, COLORS["surface_muted"])
                x = (THUMBNAIL_SIZE[0] - thumbnail.width) // 2
                y = (THUMBNAIL_SIZE[1] - thumbnail.height) // 2
                plate.alpha_composite(thumbnail, (x, y))
                photo = PIL.ImageTk.PhotoImage(plate)
                result = (photo, f"{width} × {height} px")
        except (OSError, PIL.UnidentifiedImageError):
            plate = PIL.Image.new("RGBA", THUMBNAIL_SIZE, COLORS["surface_muted"])
            photo = PIL.ImageTk.PhotoImage(plate)
            result = (photo, "Não foi possível carregar")

        self.thumbnail_photos[image_path] = result
        return result

    def _update_card_appearance(self, image_path):
        card = self.card_frames.get(image_path)
        if not card:
            return
        is_selected = image_path == self.selected_path
        color = COLORS["primary"] if is_selected else COLORS["border"]
        card.configure(
            highlightbackground=color,
            highlightcolor=color,
            highlightthickness=2 if is_selected else 1,
        )

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if getattr(event, "num", None) == 4:
            direction = -1
        elif getattr(event, "num", None) == 5:
            direction = 1
        else:
            direction = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(direction, "units")

    def focus_gallery(self):
        self.canvas.focus_set()
