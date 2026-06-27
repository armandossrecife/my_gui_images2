"""Fachada e composição principal da interface gráfica."""

import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import entidades
from ui.download_panel import DownloadPanel
from ui.gallery_panel import GalleryPanel
from ui.helpers import (
    calculate_fit_scale,
    calculate_grid_columns,
    calculate_safe_zoom_limit,
    format_bytes,
)
from ui.image_viewer import ImageViewerPanel
from ui.theme import AppTheme, Tooltip


IMAGE_DIRECTORY = Path(__file__).resolve().parent / "imagens"

__all__ = [
    "AppTheme",
    "DownloadPanel",
    "EntradaWindow",
    "GalleryPanel",
    "ImageViewerPanel",
    "MenuWindow",
    "ViewAllImagesWindow",
    "WindowImageViewer",
    "calculate_fit_scale",
    "calculate_grid_columns",
    "calculate_safe_zoom_limit",
    "format_bytes",
]


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
            self.download_panel.set_status(
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
