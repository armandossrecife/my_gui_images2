import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import PIL.Image
import PIL.ImageTk

from .constants import COLORS, FONT_FAMILY
from .helpers import (
    calculate_fit_scale,
    calculate_safe_zoom_limit,
    format_bytes,
)
from .theme import Tooltip


class ImageViewerPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Surface.TFrame", padding=(10, 18, 18, 12))
        self.image_path = None
        self.original_image = None
        self.photo_image = None
        self.scale = 1.0
        self.fit_mode = True
        self._render_job = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_widgets()

    def _build_widgets(self):
        toolbar = ttk.Frame(self, style="Surface.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(0, weight=1)

        title_area = ttk.Frame(toolbar, style="Surface.TFrame")
        title_area.grid(row=0, column=0, sticky="w")
        self.title_label = ttk.Label(
            title_area, text="Visualização", style="Section.TLabel"
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.info_label = ttk.Label(
            title_area, text="Selecione uma imagem", style="Muted.TLabel"
        )
        self.info_label.grid(row=1, column=0, sticky="w", pady=(3, 0))

        controls = ttk.Frame(toolbar, style="Surface.TFrame")
        controls.grid(row=0, column=1, sticky="e")
        self.zoom_out_button = ttk.Button(
            controls,
            text="−",
            width=3,
            style="Toolbar.TButton",
            command=self.zoom_out,
            state="disabled",
        )
        self.zoom_out_button.grid(row=0, column=0, padx=(0, 5))
        self.zoom_label = ttk.Label(
            controls, text="—", style="Body.TLabel", width=7, anchor="center"
        )
        self.zoom_label.grid(row=0, column=1, padx=2)
        self.zoom_in_button = ttk.Button(
            controls,
            text="+",
            width=3,
            style="Toolbar.TButton",
            command=self.zoom_in,
            state="disabled",
        )
        self.zoom_in_button.grid(row=0, column=2, padx=(5, 8))
        self.actual_size_button = ttk.Button(
            controls,
            text="100%",
            style="Toolbar.TButton",
            command=self.actual_size,
            state="disabled",
        )
        self.actual_size_button.grid(row=0, column=3, padx=(0, 5))
        self.fit_button = ttk.Button(
            controls,
            text="Ajustar",
            style="Toolbar.TButton",
            command=self.fit_to_window,
            state="disabled",
        )
        self.fit_button.grid(row=0, column=4)
        Tooltip(self.zoom_out_button, "Reduzir zoom (Ctrl+-)")
        Tooltip(self.zoom_in_button, "Aumentar zoom (Ctrl++)")
        Tooltip(self.actual_size_button, "Mostrar em tamanho real (Ctrl+0)")
        Tooltip(self.fit_button, "Ajustar à janela (Ctrl+F)")

        viewer = ttk.Frame(self, style="Muted.TFrame")
        viewer.grid(row=1, column=0, sticky="nsew")
        viewer.rowconfigure(0, weight=1)
        viewer.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            viewer,
            background="#E7EBF2",
            highlightthickness=0,
            bd=0,
            cursor="fleur",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vertical_scrollbar = ttk.Scrollbar(
            viewer,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            style="App.Vertical.TScrollbar",
        )
        self.vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        self.horizontal_scrollbar = ttk.Scrollbar(
            viewer,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview,
            style="App.Horizontal.TScrollbar",
        )
        self.horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(
            yscrollcommand=self.vertical_scrollbar.set,
            xscrollcommand=self.horizontal_scrollbar.set,
        )
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._pan)

        self.empty_label = tk.Label(
            self.canvas,
            text="Selecione uma imagem na biblioteca\npara visualizá-la aqui.",
            background="#E7EBF2",
            foreground=COLORS["text_muted"],
            font=(FONT_FAMILY, 13),
            justify="center",
        )
        self.empty_window = self.canvas.create_window(
            0, 0, anchor="center", window=self.empty_label
        )

    def show_image(self, image_path):
        try:
            with PIL.Image.open(image_path) as image:
                self.original_image = image.copy()
        except (OSError, PIL.UnidentifiedImageError) as error:
            messagebox.showerror(
                "Não foi possível abrir a imagem",
                str(error),
                parent=self.winfo_toplevel(),
            )
            return

        self.image_path = os.fspath(image_path)
        self.title_label.configure(text=Path(image_path).name)
        width, height = self.original_image.size
        try:
            file_size = Path(image_path).stat().st_size
            size_text = format_bytes(file_size)
        except OSError:
            size_text = "tamanho indisponível"
        self.info_label.configure(text=f"{width} × {height} px · {size_text}")
        self._set_controls_state("normal")
        self.fit_to_window()

    def fit_to_window(self):
        if not self.original_image:
            return
        viewport = self._viewport_size()
        self.scale = calculate_fit_scale(self.original_image.size, viewport)
        self.fit_mode = True
        self._render()

    def actual_size(self):
        if not self.original_image:
            return
        self.fit_mode = False
        self.scale = min(1.0, calculate_safe_zoom_limit(self.original_image.size))
        self._render()

    def zoom_in(self):
        if not self.original_image:
            return
        self.fit_mode = False
        limit = calculate_safe_zoom_limit(self.original_image.size)
        self.scale = min(limit, self.scale * 1.25)
        self._render()

    def zoom_out(self):
        if not self.original_image:
            return
        self.fit_mode = False
        self.scale = max(0.05, self.scale / 1.25)
        self._render()

    def _render(self):
        if not self.original_image:
            return

        width = max(1, round(self.original_image.width * self.scale))
        height = max(1, round(self.original_image.height * self.scale))
        if (width, height) == self.original_image.size:
            rendered = self.original_image
        else:
            rendered = self.original_image.resize(
                (width, height), PIL.Image.Resampling.LANCZOS
            )

        self.photo_image = PIL.ImageTk.PhotoImage(rendered)
        self.canvas.delete("preview")
        viewport_width, viewport_height = self._viewport_size(include_padding=False)
        x = max(viewport_width // 2, width // 2 + 22)
        y = max(viewport_height // 2, height // 2 + 22)
        self.canvas.create_image(
            x, y, anchor="center", image=self.photo_image, tags="preview"
        )
        scroll_width = max(viewport_width, width + 44)
        scroll_height = max(viewport_height, height + 44)
        self.canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))
        self.canvas.itemconfigure(self.empty_window, state="hidden")
        self.canvas.xview_moveto(0.5 - viewport_width / (2 * scroll_width))
        self.canvas.yview_moveto(0.5 - viewport_height / (2 * scroll_height))
        self.zoom_label.configure(text=f"{self.scale * 100:.0f}%")

    def _viewport_size(self, include_padding=True):
        self.update_idletasks()
        padding = 44 if include_padding else 0
        return (
            max(100, self.canvas.winfo_width() - padding),
            max(100, self.canvas.winfo_height() - padding),
        )

    def _on_canvas_resize(self, event):
        self.canvas.coords(self.empty_window, event.width // 2, event.height // 2)
        if not self.original_image or not self.fit_mode:
            return
        if self._render_job:
            self.after_cancel(self._render_job)
        self._render_job = self.after(90, self.fit_to_window)

    def _start_pan(self, event):
        if self.original_image:
            self.canvas.scan_mark(event.x, event.y)

    def _pan(self, event):
        if self.original_image:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _set_controls_state(self, state):
        for button in (
            self.zoom_out_button,
            self.zoom_in_button,
            self.actual_size_button,
            self.fit_button,
        ):
            button.configure(state=state)
