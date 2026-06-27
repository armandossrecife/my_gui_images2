import math
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import PIL.Image
import PIL.ImageTk

import entidades


IMAGE_DIRECTORY = Path(__file__).resolve().parent / "imagens"

COLORS = {
    "background": "#F4F6FA",
    "surface": "#FFFFFF",
    "surface_muted": "#EEF2F7",
    "border": "#D9E0EA",
    "text": "#172033",
    "text_muted": "#667085",
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "primary_soft": "#EEF2FF",
    "success": "#067647",
    "success_soft": "#ECFDF3",
    "danger": "#B42318",
    "danger_soft": "#FEF3F2",
    "warning": "#B54708",
}

FONT_FAMILY = "TkDefaultFont"
THUMBNAIL_SIZE = (152, 112)
MAX_RENDER_PIXELS = 36_000_000


def format_bytes(size):
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MiB"
    if size >= 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size} B"


def calculate_grid_columns(width, card_width=176):
    return max(1, int(max(width, card_width) // card_width))


def calculate_fit_scale(image_size, viewport_size, allow_upscale=False):
    image_width, image_height = image_size
    viewport_width, viewport_height = viewport_size
    if min(image_width, image_height, viewport_width, viewport_height) <= 0:
        return 1.0

    scale = min(viewport_width / image_width, viewport_height / image_height)
    return scale if allow_upscale else min(scale, 1.0)


def calculate_safe_zoom_limit(image_size, max_pixels=MAX_RENDER_PIXELS):
    width, height = image_size
    if width <= 0 or height <= 0:
        return 4.0
    return max(0.05, min(4.0, math.sqrt(max_pixels / (width * height))))


class AppTheme:
    @staticmethod
    def apply(root):
        root.configure(background=COLORS["background"])
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(".", font=(FONT_FAMILY, 11))
        style.configure("App.TFrame", background=COLORS["background"])
        style.configure("Surface.TFrame", background=COLORS["surface"])
        style.configure("Muted.TFrame", background=COLORS["surface_muted"])

        style.configure(
            "Title.TLabel",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=(FONT_FAMILY, 23, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["background"],
            foreground=COLORS["text_muted"],
            font=(FONT_FAMILY, 11),
        )
        style.configure(
            "Section.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=(FONT_FAMILY, 15, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
        )
        style.configure(
            "Muted.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text_muted"],
        )
        style.configure(
            "Badge.TLabel",
            background=COLORS["primary_soft"],
            foreground=COLORS["primary"],
            padding=(9, 4),
            font=(FONT_FAMILY, 10, "bold"),
        )
        style.configure(
            "Success.TLabel",
            background=COLORS["success_soft"],
            foreground=COLORS["success"],
            padding=(9, 6),
        )
        style.configure(
            "Error.TLabel",
            background=COLORS["danger_soft"],
            foreground=COLORS["danger"],
            padding=(9, 6),
        )
        style.configure(
            "Status.TLabel",
            background=COLORS["surface_muted"],
            foreground=COLORS["text_muted"],
            padding=(9, 6),
        )

        style.configure(
            "Primary.TButton",
            background=COLORS["primary"],
            foreground="#FFFFFF",
            bordercolor=COLORS["primary"],
            lightcolor=COLORS["primary"],
            darkcolor=COLORS["primary"],
            padding=(17, 10),
            font=(FONT_FAMILY, 11, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[
                ("disabled", "#A5B4FC"),
                ("active", COLORS["primary_hover"]),
            ],
            bordercolor=[
                ("disabled", "#A5B4FC"),
                ("active", COLORS["primary_hover"]),
            ],
        )
        style.configure(
            "Secondary.TButton",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=(13, 9),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", COLORS["surface_muted"])],
        )
        style.configure(
            "Toolbar.TButton",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=(10, 7),
        )
        style.map(
            "Toolbar.TButton",
            background=[("active", COLORS["surface_muted"])],
        )
        style.configure(
            "App.TEntry",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            insertcolor=COLORS["text"],
            padding=(10, 10),
        )
        style.map(
            "App.TEntry",
            bordercolor=[("focus", COLORS["primary"])],
            lightcolor=[("focus", COLORS["primary"])],
            darkcolor=[("focus", COLORS["primary"])],
        )
        style.configure(
            "Placeholder.TEntry",
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text_muted"],
            bordercolor=COLORS["border"],
            insertcolor=COLORS["text"],
            padding=(10, 10),
        )
        style.map(
            "Placeholder.TEntry",
            bordercolor=[("focus", COLORS["primary"])],
            lightcolor=[("focus", COLORS["primary"])],
            darkcolor=[("focus", COLORS["primary"])],
        )
        style.configure(
            "Download.Horizontal.TProgressbar",
            background=COLORS["primary"],
            troughcolor=COLORS["surface_muted"],
            bordercolor=COLORS["surface_muted"],
            lightcolor=COLORS["primary"],
            darkcolor=COLORS["primary"],
            thickness=7,
        )
        style.configure(
            "App.Horizontal.TScrollbar",
            background=COLORS["border"],
            troughcolor=COLORS["surface"],
            bordercolor=COLORS["surface"],
            arrowcolor=COLORS["text_muted"],
        )
        style.configure(
            "App.Vertical.TScrollbar",
            background=COLORS["border"],
            troughcolor=COLORS["surface"],
            bordercolor=COLORS["surface"],
            arrowcolor=COLORS["text_muted"],
        )
        style.configure(
            "App.TPanedwindow",
            background=COLORS["background"],
            sashwidth=7,
        )


class Tooltip:
    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def _schedule(self, _event=None):
        self.hide()
        self.after_id = self.widget.after(self.delay, self.show)

    def show(self):
        self.after_id = None
        if self.tip_window or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 7
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tip_window,
            text=self.text,
            background=COLORS["text"],
            foreground="#FFFFFF",
            padx=8,
            pady=5,
            font=(FONT_FAMILY, 9),
        ).pack()

    def hide(self, _event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class DownloadPanel(ttk.Frame):
    def __init__(self, parent, image_directory, on_success):
        super().__init__(parent, style="Surface.TFrame", padding=20)
        self.image_directory = Path(image_directory)
        self.on_success = on_success
        self.utilidades = entidades.Util()
        self.download_thread = None
        self.download_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.closed = False

        self.columnconfigure(0, weight=1)
        self._build_widgets()

    def _build_widgets(self):
        heading = ttk.Frame(self, style="Surface.TFrame")
        heading.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 13))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="Baixar nova imagem", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            heading,
            text="JPG, PNG, GIF, BMP ou WebP · até 25 MiB",
            style="Muted.TLabel",
        ).grid(row=0, column=1, sticky="e")

        self.url_entry = ttk.Entry(self, style="Placeholder.TEntry")
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.url_entry.insert(0, "Cole a URL direta da imagem")
        self.url_entry.bind("<FocusIn>", self._clear_placeholder)
        self.url_entry.bind("<FocusOut>", self._restore_placeholder)
        self.url_entry.bind("<Return>", lambda _event: self.download_image())

        self.download_button = ttk.Button(
            self,
            text="Baixar imagem",
            style="Primary.TButton",
            command=self.download_image,
        )
        self.download_button.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        self.cancel_button = ttk.Button(
            self,
            text="Cancelar",
            style="Secondary.TButton",
            command=self.cancel_download,
            state="disabled",
        )
        self.cancel_button.grid(row=1, column=2, sticky="ew")

        progress_frame = ttk.Frame(self, style="Surface.TFrame")
        progress_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(13, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="Download.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.progress_label = ttk.Label(
            progress_frame, text="", style="Muted.TLabel", width=24, anchor="e"
        )
        self.progress_label.grid(row=0, column=1, sticky="e")

        self.status_label = ttk.Label(
            self,
            text="Informe uma URL direta para começar.",
            style="Status.TLabel",
            anchor="w",
        )
        self.status_label.grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=(11, 0)
        )

    def _clear_placeholder(self, _event=None):
        if self.url_entry.get() == "Cole a URL direta da imagem":
            self.url_entry.delete(0, tk.END)
            self.url_entry.configure(style="App.TEntry")

    def _restore_placeholder(self, _event=None):
        if not self.url_entry.get().strip():
            self.url_entry.insert(0, "Cole a URL direta da imagem")
            self.url_entry.configure(style="Placeholder.TEntry")

    def focus_url(self):
        self._clear_placeholder()
        self.url_entry.focus_set()

    def download_image(self):
        if self.download_thread and self.download_thread.is_alive():
            return

        self._reset_progress()
        url = self.url_entry.get().strip()
        if not url or url == "Cole a URL direta da imagem":
            self._set_status("Informe a URL da imagem.", "error")
            self.focus_url()
            return

        try:
            os.makedirs(self.image_directory, exist_ok=True)
            nome, extensao = self.utilidades.extrair_nome_extensao_url(url)
            filename = self.utilidades.criar_nome_unico(
                self.image_directory, nome, extensao
            )
        except ValueError as error:
            self._set_status(str(error), "error")
            return
        except OSError as error:
            self._set_status(f"Não foi possível preparar o arquivo: {error}", "error")
            return

        filename_path = os.path.join(self.image_directory, filename)
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.url_entry.configure(state="disabled")
        self.cancel_event = threading.Event()
        self._start_progress()
        self._set_status("Conectando ao servidor…", "status")

        self.download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, filename_path, self.cancel_event),
            daemon=True,
        )
        self.download_thread.start()
        self.after(100, self._check_download_queue)

    def _download_worker(self, url, filename_path, cancel_event):
        try:
            download = entidades.Download(
                url, filename_path, cancel_event=cancel_event
            )
            download.set_callback(
                lambda total, current: self.download_queue.put(
                    ("progress", total, current)
                )
            )
            download.executa()
        except Exception as error:
            self.download_queue.put(("finished", None, error))
            return

        self.download_queue.put(("finished", filename_path, None))

    def _check_download_queue(self):
        if self.closed:
            return

        while True:
            try:
                event = self.download_queue.get_nowait()
            except queue.Empty:
                if self.download_thread and self.download_thread.is_alive():
                    self.after(100, self._check_download_queue)
                return

            event_type = event[0]
            if event_type == "progress":
                _, total_size, downloaded_size = event
                self._update_progress(total_size, downloaded_size)
                continue

            _, filename_path, error = event
            self._download_finished(filename_path, error)
            return

    def _download_finished(self, filename_path, error):
        self.download_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.url_entry.configure(state="normal")
        self.progress_bar.stop()

        if error:
            self._reset_progress()
            if isinstance(error, entidades.DownloadCancelado):
                self._set_status("Download cancelado.", "status")
            else:
                self._set_status(f"Erro no download: {error}", "error")
            return

        self.progress_bar.configure(mode="determinate", maximum=100, value=100)
        self.progress_label.configure(text="100% concluído")
        self._set_status(
            f"Imagem salva com sucesso: {Path(filename_path).name}", "success"
        )
        self.on_success(filename_path)

    def _start_progress(self):
        self.progress_bar.configure(mode="indeterminate", maximum=100, value=0)
        self.progress_bar.start(10)
        self.progress_label.configure(text="Conectando…")

    def _reset_progress(self):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate", maximum=100, value=0)
        self.progress_label.configure(text="")

    def _update_progress(self, total_size, downloaded_size):
        if total_size > 0:
            self.progress_bar.stop()
            self.progress_bar.configure(
                mode="determinate",
                maximum=total_size,
                value=min(downloaded_size, total_size),
            )
            percentage = min(downloaded_size / total_size * 100, 100)
            self.progress_label.configure(
                text=(
                    f"{percentage:.0f}% · {format_bytes(downloaded_size)} "
                    f"de {format_bytes(total_size)}"
                )
            )
            self._set_status("Baixando e validando a imagem…", "status")
            return

        self.progress_label.configure(text=f"{format_bytes(downloaded_size)} baixados")
        self._set_status("Baixando e validando a imagem…", "status")

    def _set_status(self, text, kind):
        style = {
            "success": "Success.TLabel",
            "error": "Error.TLabel",
            "status": "Status.TLabel",
        }[kind]
        self.status_label.configure(text=text, style=style)

    def cancel_download(self):
        if self.download_thread and self.download_thread.is_alive():
            self.cancel_event.set()
            self.cancel_button.configure(state="disabled")
            self._set_status("Cancelando o download…", "status")

    def close(self):
        self.closed = True
        self.cancel_event.set()
        self.progress_bar.stop()


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


class MenuWindow:
    def __init__(self, my_app, my_title, image_directory=IMAGE_DIRECTORY) -> None:
        self.app = my_app
        self.app.title(my_title)
        self.app.geometry("1180x760")
        self.app.minsize(900, 620)
        self.image_directory = Path(image_directory)
        self.last_image = None
        self.image_paths = []

        AppTheme.apply(self.app)
        self._build_layout()
        self._bind_shortcuts()
        self.load_images(select_latest=True)
        self.app.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_layout(self):
        container = ttk.Frame(self.app, style="App.TFrame", padding=22)
        container.pack(expand=True, fill=tk.BOTH)
        container.rowconfigure(2, weight=1)
        container.columnconfigure(0, weight=1)

        header = ttk.Frame(container, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.columnconfigure(0, weight=1)
        title_area = ttk.Frame(header, style="App.TFrame")
        title_area.grid(row=0, column=0, sticky="w")
        ttk.Label(title_area, text="Minhas imagens", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            title_area,
            text="Baixe, organize e visualize sua biblioteca em um só lugar.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.latest_button = ttk.Button(
            header,
            text="Ir para a mais recente",
            style="Secondary.TButton",
            command=self.carrega_view_image,
        )
        self.latest_button.grid(row=0, column=1, rowspan=2, sticky="e")
        Tooltip(self.latest_button, "Selecionar a imagem baixada mais recentemente")

        self.download_panel = DownloadPanel(
            container,
            image_directory=self.image_directory,
            on_success=self._download_succeeded,
        )
        self.download_panel.grid(row=1, column=0, sticky="ew", pady=(0, 18))

        content = ttk.Panedwindow(
            container, orient=tk.HORIZONTAL, style="App.TPanedwindow"
        )
        content.grid(row=2, column=0, sticky="nsew")

        self.gallery = GalleryPanel(content, on_select=self._select_image)
        self.viewer = ImageViewerPanel(content)
        content.add(self.gallery, weight=2)
        content.add(self.viewer, weight=3)

    def _bind_shortcuts(self):
        self.app.bind("<Control-l>", lambda _event: self.carrega_janela_entrada())
        self.app.bind("<Control-L>", lambda _event: self.carrega_janela_entrada())
        self.app.bind("<Control-plus>", lambda _event: self.viewer.zoom_in())
        self.app.bind("<Control-equal>", lambda _event: self.viewer.zoom_in())
        self.app.bind("<Control-minus>", lambda _event: self.viewer.zoom_out())
        self.app.bind("<Control-0>", lambda _event: self.viewer.actual_size())
        self.app.bind("<Control-f>", lambda _event: self.viewer.fit_to_window())
        self.app.bind("<Escape>", lambda _event: self.download_panel.cancel_download())

    def carrega_janela_entrada(self):
        self.download_panel.focus_url()

    def carrega_view_image(self):
        self.load_images()
        if not self.image_paths:
            self.download_panel.focus_url()
            self.download_panel._set_status(
                "Baixe sua primeira imagem para visualizá-la.", "status"
            )
            return
        self.gallery.select_path(self.image_paths[-1])

    def carrega_view_all_images(self):
        self.load_images()
        self.gallery.focus_gallery()

    def load_images(self, select_latest=False):
        self.image_paths = entidades.Util().list_files_by_date(self.image_directory)
        selected = self.gallery.selected_path
        if selected not in self.image_paths:
            selected = self.image_paths[-1] if self.image_paths and select_latest else None
        self.gallery.set_images(self.image_paths, selected_path=selected)
        self.latest_button.configure(
            state="normal" if self.image_paths else "disabled"
        )
        if selected:
            self._select_image(selected)

    def _select_image(self, image_path):
        self.last_image = os.fspath(image_path)
        self.viewer.show_image(image_path)

    def _download_succeeded(self, filename_path):
        self.last_image = os.fspath(filename_path)
        self.load_images()
        self.gallery.select_path(filename_path)

    def destroy(self):
        self.download_panel.close()
        self.app.destroy()


class WindowImageViewer:
    """Visualizador independente mantido para compatibilidade com a API original."""

    def __init__(self, image_path, parent, on_close=None):
        self.on_close = on_close
        if not os.path.exists(image_path):
            messagebox.showerror(
                "Erro", "A imagem não foi encontrada.", parent=parent
            )
            self._notify_close()
            return

        self.app = tk.Toplevel(parent)
        self.app.title(Path(image_path).name)
        self.app.geometry("900x650")
        self.app.minsize(620, 460)
        AppTheme.apply(self.app)
        self.viewer = ImageViewerPanel(self.app)
        self.viewer.pack(expand=True, fill=tk.BOTH, padx=12, pady=12)
        self.viewer.show_image(image_path)
        self.app.protocol("WM_DELETE_WINDOW", self.destroy)

    def destroy(self):
        self._notify_close()
        self.app.destroy()

    def _notify_close(self):
        if self.on_close:
            self.on_close()
            self.on_close = None


class EntradaWindow:
    """Adaptador para chamadas antigas: direciona o foco ao novo formulário."""

    def __init__(self, menu_window):
        self.menu_window = menu_window
        self.app = menu_window.app
        menu_window.carrega_janela_entrada()

    def destroy(self):
        return None


class ViewAllImagesWindow:
    """Adaptador para chamadas antigas: direciona o foco à nova biblioteca."""

    def __init__(self, menu_window):
        self.menu_window = menu_window
        self.app = menu_window.app
        menu_window.carrega_view_all_images()

    def destroy(self):
        return None
