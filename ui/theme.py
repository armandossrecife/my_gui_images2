import tkinter as tk
from tkinter import ttk

from .constants import COLORS, FONT_FAMILY


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
