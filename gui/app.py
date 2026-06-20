# -*- coding: utf-8 -*-
"""
SFM Community Patcher v3.0 — Main GUI Application.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

from .about import AboutWindow
from .log_widget import LogWidget
from .styles import (
    ACCENT, ACCENT_HOVER, BG, BG_SECONDARY, BG_INPUT, BORDER,
    BUTTON_HEIGHT, FG, FG_DIM, FONT_BUTTON, FONT_LABEL, FONT_SMALL, FONT_TITLE,
    PADDING, SUCCESS, WARNING, WINDOW_HEIGHT, WINDOW_WIDTH,
)

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from core.sfm_detector import detect_sfm_game_dir, validate_game_dir
from core.setup import SetupConfig, SetupResult, run_setup


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SFM Community Patcher v3.0")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._center_window()
        self._build_ui()
        self._detect_sfm()

    def _center_window(self) -> None:
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        main = tk.Frame(self.root, bg=BG, padx=PADDING, pady=PADDING)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main, text="SFM Community Patcher", font=FONT_TITLE,
            bg=BG, fg=FG,
        )
        title.pack(anchor=tk.W)
        subtitle = tk.Label(
            main, text="Engine stability & Vulkan graphics for Source Filmmaker",
            font=("Segoe UI", 9), bg=BG, fg=FG_DIM,
        )
        subtitle.pack(anchor=tk.W, pady=(0, PADDING))

        # SFM Path
        path_frame = tk.Frame(main, bg=BG)
        path_frame.pack(fill=tk.X, pady=(0, PADDING))

        tk.Label(path_frame, text="SFM Path:", font=FONT_LABEL, bg=BG, fg=FG).pack(anchor=tk.W)

        input_row = tk.Frame(path_frame, bg=BG)
        input_row.pack(fill=tk.X, pady=(4, 0))

        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(
            input_row, textvariable=self.path_var, font=FONT_LABEL,
            bg=BG_INPUT, fg=FG, insertbackground=FG,
            highlightbackground=BORDER, highlightthickness=1,
            relief=tk.FLAT,
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        self.browse_btn = tk.Button(
            input_row, text="...", font=FONT_BUTTON,
            bg=BG_SECONDARY, fg=FG, activebackground=BORDER, activeforeground=FG,
            relief=tk.FLAT, padx=8, cursor="hand2",
            command=self._browse,
        )
        self.browse_btn.pack(side=tk.RIGHT, padx=(4, 0))

        self.status_label = tk.Label(
            main, text="", font=("Segoe UI", 9), bg=BG, fg=FG_DIM,
        )
        self.status_label.pack(anchor=tk.W, pady=(0, PADDING))

        # Options
        options_frame = tk.LabelFrame(
            main, text="  Installation Options  ", font=FONT_LABEL,
            bg=BG, fg=FG, labelanchor=tk.NW,
            highlightbackground=BORDER, highlightthickness=1,
            padx=PADDING, pady=PADDING,
        )
        options_frame.pack(fill=tk.X, pady=(0, PADDING))

        self.dxvk_var = tk.BooleanVar(value=True)
        self.reshade_var = tk.BooleanVar(value=True)
        self.patches_var = tk.BooleanVar(value=True)
        self.edicts_var = tk.BooleanVar(value=False)

        checks = [
            ("Install DXVK (Vulkan renderer)", self.dxvk_var),
            ("Install ReShade (post-processing effects)", self.reshade_var),
            ("Apply engine patches (hunk, rbtree, etc.)", self.patches_var),
            ("Experimental: edict limit (risky, can break lightmaps)", self.edicts_var),
        ]
        for text, var in checks:
            cb = tk.Checkbutton(
                options_frame, text=text, variable=var,
                font=FONT_LABEL, bg=BG, fg=FG,
                selectcolor=BG_INPUT, activebackground=BG, activeforeground=FG,
                highlightthickness=0,
            )
            cb.pack(anchor=tk.W, pady=2)

        # Buttons
        btn_frame = tk.Frame(main, bg=BG)
        btn_frame.pack(fill=tk.X, pady=(0, PADDING))

        self.install_btn = tk.Button(
            btn_frame, text="Install All", font=FONT_BUTTON,
            bg=ACCENT, fg="#1e1e2e", activebackground=ACCENT_HOVER,
            activeforeground="#1e1e2e", relief=tk.FLAT,
            padx=20, pady=6, cursor="hand2",
            command=self._run_install,
        )
        self.install_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.dryrun_btn = tk.Button(
            btn_frame, text="Dry Run", font=FONT_BUTTON,
            bg=BG_SECONDARY, fg=FG, activebackground=BORDER, activeforeground=FG,
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
            command=self._run_dryrun,
        )
        self.dryrun_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.restore_btn = tk.Button(
            btn_frame, text="Restore", font=FONT_BUTTON,
            bg=BG_SECONDARY, fg=WARNING, activebackground=BORDER, activeforeground=WARNING,
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
            command=self._run_restore,
        )
        self.restore_btn.pack(side=tk.LEFT)

        self.about_btn = tk.Button(
            btn_frame, text="About", font=FONT_SMALL,
            bg=BG_SECONDARY, fg=FG_DIM, activebackground=BORDER, activeforeground=FG,
            relief=tk.FLAT, padx=8, pady=2, cursor="hand2",
            command=self._show_about,
        )
        self.about_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.status_bottom = tk.Label(
            btn_frame, text="Ready", font=("Segoe UI", 9),
            bg=BG, fg=SUCCESS, anchor=tk.E,
        )
        self.status_bottom.pack(side=tk.RIGHT)

        # Log
        self.log_widget = LogWidget(main)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def _browse(self) -> None:
        path = filedialog.askdirectory(title="Select SFM game directory")
        if path:
            self.path_var.set(path)
            self._validate_path(path)

    def _detect_sfm(self) -> None:
        self.log_widget.append("Searching for Source Filmmaker...", "dim")
        detected = detect_sfm_game_dir()
        if detected:
            self.path_var.set(detected)
            self._validate_path(detected)
        else:
            self.status_label.config(text="SFM not found — click ... to browse", fg=WARNING)
            self.log_widget.append("Source Filmmaker not found automatically.", "warning")

    def _validate_path(self, path: str) -> None:
        valid, msg = validate_game_dir(path)
        if valid:
            self.status_label.config(text=f"Found: {path}", fg=SUCCESS)
            self.log_widget.clear()
            self.log_widget.append(f"SFM found: {path}", "success")
        else:
            self.status_label.config(text=msg, fg="#f38ba8")

    def _make_config(self, dry_run: bool = False) -> Optional[SetupConfig]:
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("No path", "Please specify the SFM game directory.")
            return None

        valid, msg = validate_game_dir(path)
        if not valid:
            messagebox.showerror("Invalid path", msg)
            return None

        return SetupConfig(
            game_dir=path,
            install_dxvk=self.dxvk_var.get(),
            install_reshade=self.reshade_var.get(),
            apply_patches=self.patches_var.get(),
            apply_edicts=self.edicts_var.get(),
            dry_run=dry_run,
        )

    def _set_buttons_state(self, state: str) -> None:
        for btn in [self.install_btn, self.dryrun_btn, self.restore_btn, self.browse_btn]:
            btn.config(state=state)

    def _run_in_thread(self, func) -> None:
        self._set_buttons_state(tk.DISABLED)
        self.status_bottom.config(text="Running...", fg=ACCENT)
        thread = threading.Thread(target=func, daemon=True)
        thread.start()

    def _on_done(self, result: Optional[SetupResult] = None) -> None:
        self._set_buttons_state(tk.NORMAL)
        if result and result.success:
            self.status_bottom.config(text="Done", fg=SUCCESS)
        elif result:
            self.status_bottom.config(text="Completed with errors", fg=WARNING)
        else:
            self.status_bottom.config(text="Ready", fg=SUCCESS)

    def _run_install(self) -> None:
        config = self._make_config(dry_run=False)
        if not config:
            return

        self.log_widget.clear()
        self.log_widget.append("Starting installation...", "accent")

        def _worker():
            result = run_setup(config, log_cb=self.log_widget.log)
            self.root.after(0, self._on_done, result)

        self._run_in_thread(_worker)

    def _run_dryrun(self) -> None:
        config = self._make_config(dry_run=True)
        if not config:
            return

        self.log_widget.clear()
        self.log_widget.append("Starting dry run (no files modified)...", "accent")

        def _worker():
            result = run_setup(config, log_cb=self.log_widget.log)
            self.root.after(0, self._on_done, result)

        self._run_in_thread(_worker)

    def _run_restore(self) -> None:
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("No path", "Please specify the SFM game directory.")
            return

        bin_dir = os.path.join(path, "bin")
        backups_dir = os.path.join(bin_dir, "backups")

        if not os.path.isdir(backups_dir):
            messagebox.showinfo("No backups", "No backups found in bin\\backups\\")
            return

        if not messagebox.askyesno("Restore", "Restore all DLLs from bin\\backups\\?"):
            return

        self.log_widget.clear()
        self.log_widget.append("Restoring from backups...", "accent")

        import shutil
        restored = 0
        for name in os.listdir(backups_dir):
            src = os.path.join(backups_dir, name)
            dst = os.path.join(bin_dir, name)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                self.log_widget.append(f"Restored: {name}", "success")
                restored += 1

        self.log_widget.append(f"\nRestored {restored} file(s) from backups.", "success")
        self._on_done(None)

    def _show_about(self) -> None:
        AboutWindow(self.root)

    def run(self) -> None:
        self.root.mainloop()
