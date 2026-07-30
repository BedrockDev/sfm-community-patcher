# -*- coding: utf-8 -*-
"""
Diagnostics window — collect and display system info.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from .styles import (
    ACCENT, BG, BG_INPUT, BORDER, FG, FG_DIM, FONT_SMALL, FONT_LOG,
)


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


def _collect(game_dir: str) -> str:
    lines = ["=== SFM Community Patcher v3.0 ===", ""]

    lines.append("OS: " + platform.system() + " " + platform.release())
    lines.append("Python: " + ("bundled" if getattr(sys, "frozen", False) else sys.version.split()[0]))

    gpu, driver = _get_gpu_info()
    lines.append("GPU: " + gpu)
    lines.append("Driver: " + driver)
    lines.append("")

    if not game_dir:
        lines.append("SFM: NOT FOUND")
        return "\n".join(lines)

    lines.append("SFM: " + game_dir)

    bin_dir = os.path.join(game_dir, "bin")
    for dll in ["engine.dll", "vstdlib.dll", "shaderapidx9.dll"]:
        path = os.path.join(bin_dir, dll)
        if os.path.isfile(path):
            lines.append("  " + dll + ": " + str(os.path.getsize(path)) + " bytes")
        else:
            lines.append("  " + dll + ": NOT FOUND")

    lines.append("")
    lines.append("DXVK: " + ("Yes" if os.path.isfile(os.path.join(bin_dir, "d3d9_vlk.dll")) else "No"))

    d3d9 = os.path.join(bin_dir, "d3d9.dll")
    reshade = os.path.isfile(d3d9) and os.path.getsize(d3d9) > 3000000
    lines.append("ReShade: " + ("Yes" if reshade else "No"))

    ini = os.path.join(bin_dir, "ReShade.ini")
    if os.path.isfile(ini):
        with open(ini, encoding="utf-8", errors="replace") as f:
            proxy = "EnableProxyLibrary=1" in f.read()
        lines.append("Proxy: " + ("Yes" if proxy else "No"))
    else:
        lines.append("Proxy: No ReShade.ini")

    lines.append("")
    patches = _check_patches(bin_dir)
    if patches:
        lines.append("Patches: " + ", ".join(patches))
    else:
        lines.append("Patches: None detected")

    return "\n".join(lines)


class DiagnosticsWindow:
    def __init__(self, parent: tk.Tk, game_dir: str = "") -> None:
        self.win = tk.Toplevel(parent)
        self.win.title("Diagnostics")
        self.win.configure(bg=BG)
        self.win.resizable(True, True)
        self.win.grab_set()
        self.win.geometry("600x500")

        self._game_dir = game_dir

        header = tk.Frame(self.win, bg=BG, padx=12, pady=(12, 0))
        header.pack(fill=tk.X)

        tk.Label(
            header, text="System Diagnostics", font=("Segoe UI", 14, "bold"),
            bg=BG, fg=FG,
        ).pack(anchor=tk.W)

        tk.Label(
            header, text="Copy this info when reporting issues",
            font=FONT_SMALL, bg=BG, fg=FG_DIM,
        ).pack(anchor=tk.W, pady=(2, 0))

        btn_frame = tk.Frame(self.win, bg=BG, padx=12, pady=8)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame, text="Copy to Clipboard", font=FONT_SMALL,
            bg=ACCENT, fg="#1e1e2e", activebackground="#74c7ec",
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=self._copy,
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_frame, text="Refresh", font=FONT_SMALL,
            bg=BG, fg=FG_DIM, activebackground=BORDER,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=self._do_collect,
        ).pack(side=tk.LEFT, padx=(8, 0))

        self.text = tk.Text(
            self.win, wrap=tk.WORD,
            bg=BG_INPUT, fg=FG, font=FONT_LOG,
            insertbackground=FG, selectbackground="#45475a",
            relief=tk.FLAT, padx=8, pady=8,
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.text.insert("1.0", "Loading...")
        self.text.config(state=tk.DISABLED)

        self.win.update_idletasks()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        x = (self.win.winfo_screenwidth() // 2) - (w // 2)
        y = (self.win.winfo_screenheight() // 2) - (h // 2)
        self.win.geometry(str(w) + "x" + str(h) + "+" + str(x) + "+" + str(y))

        self.win.after(100, self._do_collect)

    def _set(self, content: str) -> None:
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, content)
        self.text.config(state=tk.DISABLED)

    def _do_collect(self) -> None:
        try:
            report = _collect(self._game_dir)
            self._set(report)
        except Exception:
            self._set("ERROR:\n\n" + traceback.format_exc())

    def _copy(self) -> None:
        self.text.config(state=tk.NORMAL)
        content = self.text.get("1.0", tk.END).strip()
        self.text.config(state=tk.DISABLED)
        self.win.clipboard_clear()
        self.win.clipboard_append(content)
        self.win.update()
        messagebox.showinfo("Copied", "Paste in your bug report.", parent=self.win)
