# -*- coding: utf-8 -*-
"""
Log widget for displaying patcher output in the GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext

from .styles import BG_INPUT, FG, FG_DIM, FONT_LOG, BORDER


class LogWidget:
    """A scrollable text widget for displaying log output."""

    def __init__(self, parent: tk.Frame) -> None:
        self.frame = tk.Frame(parent, bg=BG_INPUT, highlightbackground=BORDER, highlightthickness=1)

        self.text = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=BG_INPUT,
            fg=FG,
            font=FONT_LOG,
            insertbackground=FG,
            selectbackground="#45475a",
            relief=tk.FLAT,
            padx=8,
            pady=6,
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        self.text.tag_config("info", foreground=FG)
        self.text.tag_config("success", foreground="#a6e3a1")
        self.text.tag_config("warning", foreground="#f9e2af")
        self.text.tag_config("error", foreground="#f38ba8")
        self.text.tag_config("dim", foreground=FG_DIM)
        self.text.tag_config("accent", foreground="#89b4fa")

    def pack(self, **kwargs) -> None:
        self.frame.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)

    def clear(self) -> None:
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def append(self, msg: str, tag: str = "info") -> None:
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, msg + "\n", tag)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def log(self, msg: str) -> None:
        """Callback-compatible log method."""
        if "ERROR" in msg or "failed" in msg.lower():
            self.append(msg, "error")
        elif "WARNING" in msg:
            self.append(msg, "warning")
        elif "OK" in msg or "success" in msg.lower() or "Done" in msg:
            self.append(msg, "success")
        elif ">>>" in msg or "===" in msg:
            self.append(msg, "accent")
        else:
            self.append(msg, "info")
