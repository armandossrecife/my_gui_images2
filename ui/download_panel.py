import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import entidades

from .helpers import format_bytes


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
            self.set_status("Informe a URL da imagem.", "error")
            self.focus_url()
            return

        try:
            os.makedirs(self.image_directory, exist_ok=True)
            nome, extensao = self.utilidades.extrair_nome_extensao_url(url)
            filename = self.utilidades.criar_nome_unico(
                self.image_directory, nome, extensao
            )
        except ValueError as error:
            self.set_status(str(error), "error")
            return
        except OSError as error:
            self.set_status(f"Não foi possível preparar o arquivo: {error}", "error")
            return

        filename_path = os.path.join(self.image_directory, filename)
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.url_entry.configure(state="disabled")
        self.cancel_event = threading.Event()
        self._start_progress()
        self.set_status("Conectando ao servidor…", "status")

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
                self.set_status("Download cancelado.", "status")
            else:
                self.set_status(f"Erro no download: {error}", "error")
            return

        self.progress_bar.configure(mode="determinate", maximum=100, value=100)
        self.progress_label.configure(text="100% concluído")
        self.set_status(
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
            self.set_status("Baixando e validando a imagem…", "status")
            return

        self.progress_label.configure(text=f"{format_bytes(downloaded_size)} baixados")
        self.set_status("Baixando e validando a imagem…", "status")

    def set_status(self, text, kind):
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
            self.set_status("Cancelando o download…", "status")

    def close(self):
        self.closed = True
        self.cancel_event.set()
        self.progress_bar.stop()
