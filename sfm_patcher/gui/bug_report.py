# -*- coding: utf-8 -*-
"""
Bug Report window — same pattern as About (works in frozen EXE).
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import tkinter as tk
import urllib.parse
import webbrowser
from tkinter import messagebox

from .styles import (
    ACCENT, BG, BG_INPUT, BORDER, FG, FG_DIM, FONT_BUTTON, FONT_LABEL, FONT_SMALL,
)

BUG_EMAIL = "bumazhnietanki@gmail.com"


def _get_gpu_info() -> tuple[str, str]:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object -First 1 Name,DriverVersion | ConvertTo-Json"],
            capture_output=True, text=True, timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if r.returncode == 0 and r.stdout.strip():
            import json
            data = json.loads(r.stdout)
            return data.get("Name", "?"), data.get("DriverVersion", "?")
    except Exception:
        pass
    return "?", "?"


def _check_patches(bin_dir: str) -> list[str]:
    applied = []
    engine = os.path.join(bin_dir, "engine.dll")
    if not os.path.isfile(engine):
        return applied
    try:
        with open(engine, "rb") as f:
            data = f.read()
    except Exception:
        return applied
    for name, pattern in [
        ("Hunk 2GB", b"\x3D\x00\x00\x00\x80"),
        ("Hunk 256MB", b"\x68\x00\x00\x00\x10\x68\x00\x00\x01\x00\xBE\x00\x00\x00\x10"),
        ("RBTree 31-bit", b"\x81\xE1\xFF\xFF\xFF\x7F"),
        ("FCVAR bypass", b"\xB8\x01\x00\x00\x00\xEB"),
        ("Brushes 16k", b"\x81\xFE\x00\x40\x00\x00\x7E\x0D"),
        ("Planes 128k", b"\x81\xFF\x00\x00\x02\x00\x7E\x0D"),
    ]:
        if pattern in data:
            applied.append(name)
    vstdlib = os.path.join(bin_dir, "vstdlib.dll")
    if os.path.isfile(vstdlib):
        try:
            with open(vstdlib, "rb") as f:
                if b"\x3B\x57\x08\x90\x90" in f.read():
                    applied.append("KeyValues")
        except Exception:
            pass
    return applied


def collect_diagnostics(game_dir: str) -> str:
    lines = []
    lines.append("OS: " + platform.system() + " " + platform.release())
    gpu, driver = _get_gpu_info()
    lines.append("GPU: " + gpu)
    lines.append("Driver: " + driver)
    if not game_dir:
        lines.append("SFM: NOT FOUND")
        return "\n".join(lines)
    lines.append("SFM: " + game_dir)
    bin_dir = os.path.join(game_dir, "bin")
    for dll in ["engine.dll", "vstdlib.dll", "shaderapidx9.dll"]:
        path = os.path.join(bin_dir, dll)
        if os.path.isfile(path):
            lines.append("  " + dll + ": " + str(os.path.getsize(path)))
    dxvk = os.path.isfile(os.path.join(bin_dir, "d3d9_vlk.dll"))
    d3d9 = os.path.join(bin_dir, "d3d9.dll")
    reshade = os.path.isfile(d3d9) and os.path.getsize(d3d9) > 3000000
    lines.append("DXVK: " + ("Yes" if dxvk else "No"))
    lines.append("ReShade: " + ("Yes" if reshade else "No"))
    patches = _check_patches(bin_dir)
    lines.append("Patches: " + (", ".join(patches) if patches else "None"))
    return "\n".join(lines)


class BugReportWindow:
    def __init__(self, parent: tk.Tk, game_dir: str = "") -> None:
        self.win = tk.Toplevel(parent)
        self.win.title("Bug Report")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.geometry("450x480")

        self._game_dir = game_dir
        self._build()

        self.win.update_idletasks()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        x = (self.win.winfo_screenwidth() // 2) - (w // 2)
        y = (self.win.winfo_screenheight() // 2) - (h // 2)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self) -> None:
        root = tk.Frame(self.win, bg=BG, padx=24, pady=16)
        root.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            root, text="Report a Bug", font=("Segoe UI", 14, "bold"),
            bg=BG, fg=FG,
        ).pack(anchor=tk.W)

        tk.Label(
            root, text="Describe the problem. Diagnostics auto-attached.",
            font=FONT_SMALL, bg=BG, fg=FG_DIM,
        ).pack(anchor=tk.W, pady=(2, 8))

        tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            root, text="What happened:", font=FONT_LABEL,
            bg=BG, fg=FG,
        ).pack(anchor=tk.W)

        self.desc_entry = tk.Entry(
            root, bg=BG_INPUT, fg=FG, font=("Segoe UI", 10),
            insertbackground=FG, relief=tk.FLAT,
            highlightbackground=BORDER, highlightthickness=1,
        )
        self.desc_entry.pack(fill=tk.X, ipady=4, pady=(4, 8))

        tk.Label(
            root, text="Diagnostics:", font=FONT_LABEL,
            bg=BG, fg=FG_DIM,
        ).pack(anchor=tk.W)

        diag_frame = tk.Frame(root, bg=BG_INPUT, highlightbackground=BORDER, highlightthickness=1)
        diag_frame.pack(fill=tk.X, pady=(4, 12))

        self.diag_labels = []
        self._game_dir and self._load_diag(diag_frame)

        tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 12))

        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame, text="Send Email", font=FONT_BUTTON,
            bg=ACCENT, fg="#1e1e2e", activebackground="#74c7ec",
            relief=tk.FLAT, padx=16, pady=4, cursor="hand2",
            command=self._send,
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_frame, text="Cancel", font=FONT_SMALL,
            bg=BG, fg=FG_DIM, activebackground=BORDER,
            relief=tk.FLAT, padx=8, pady=4, cursor="hand2",
            command=self.win.destroy,
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _load_diag(self, parent: tk.Frame) -> None:
        diag = collect_diagnostics(self._game_dir)
        for line in diag.split("\n"):
            lbl = tk.Label(
                parent, text=line, font=("Consolas", 8),
                bg=BG_INPUT, fg=FG_DIM, anchor=tk.W,
            )
            lbl.pack(anchor=tk.W, padx=8, pady=1)
            self.diag_labels.append(lbl)

    def _send(self) -> None:
        desc = self.desc_entry.get().strip()
        if not desc:
            messagebox.showwarning("Empty", "Describe the problem.", parent=self.win)
            return

        diag = "\n".join(l.cget("text") for l in self.diag_labels)
        body = desc + "\n\n---\n\n" + diag

        params = urllib.parse.urlencode({
            "subject": "[SFM Patcher v3.2] Bug Report",
            "body": body,
        })
        webbrowser.open("mailto:" + BUG_EMAIL + "?" + params)
        messagebox.showinfo(
            "Sent",
            "Email client opened.\nIf nothing happens, send manually to:\n" + BUG_EMAIL,
            parent=self.win,
        )
        self.win.destroy()
