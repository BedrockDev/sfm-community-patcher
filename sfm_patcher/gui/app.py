# -*- coding: utf-8 -*-
"""
SFM Community Patcher v3.2 — Main GUI Application.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

from .about import AboutWindow
from .bug_report import BugReportWindow
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
        self.root.title("SFM Community Patcher v3.2")
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
        self.hunk_var = tk.BooleanVar(value=True)
        self.rbtree_var = tk.BooleanVar(value=True)
        self.fcvar_var = tk.BooleanVar(value=True)
        self.keyvalues_var = tk.BooleanVar(value=True)
        self.brushes_var = tk.BooleanVar(value=True)
        self.planes_var = tk.BooleanVar(value=True)
        self.edicts_var = tk.BooleanVar(value=False)

        checks = [
            ("Install DXVK (Vulkan renderer)", self.dxvk_var, None),
            ("Install ReShade (post-processing)", self.reshade_var, None),
        ]
        for text, var, _ in checks:
            tk.Checkbutton(
                options_frame, text=text, variable=var,
                font=FONT_LABEL, bg=BG, fg=FG,
                selectcolor=BG_INPUT, activebackground=BG, activeforeground=FG,
                highlightthickness=0,
            ).pack(anchor=tk.W, pady=1)

        tk.Frame(options_frame, bg=BORDER, height=1).pack(fill=tk.X, pady=(6, 4))
        tk.Label(options_frame, text="Engine patches:", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(anchor=tk.W)

        patches = [
            ("Hunk memory (256 MB / 2 GB)", self.hunk_var, "Fixes 'Engine hunk overflow'. Safe."),
            ("RBTree index limit", self.rbtree_var, "Fixes 'CUtlRBTree overflow'. May cause random crashes."),
            ("FCVAR_CHEAT bypass", self.fcvar_var, "Unlocks cheat commands. Safe."),
            ("KeyValues string pool", self.keyvalues_var, "Fixes 'Out of keyvalue string space'. Safe."),
            ("Map brushes (16k)", self.brushes_var, "Fixes 'too many brushes'. Safe."),
            ("Map planes (128k)", self.planes_var, "Fixes 'too many planes'. Safe."),
            ("Edict limit (experimental)", self.edicts_var, "DANGER: can break lightmaps and cause crashes."),
        ]
        for text, var, tip in patches:
            f = tk.Frame(options_frame, bg=BG)
            f.pack(anchor=tk.W, pady=1)
            cb = tk.Checkbutton(
                f, text=text, variable=var,
                font=FONT_LABEL, bg=BG, fg=FG,
                selectcolor=BG_INPUT, activebackground=BG, activeforeground=FG,
                highlightthickness=0,
            )
            cb.pack(side=tk.LEFT)
            if tip:
                warn_color = "#f38ba8" if "DANGER" in tip or "crash" in tip.lower() else FG_DIM
                tk.Label(f, text="(!)", font=FONT_SMALL, bg=BG, fg=warn_color, cursor="hand2").pack(side=tk.LEFT, padx=(4, 0))
                tk.Label(f, text=tip, font=("Segoe UI", 7), bg=BG, fg=FG_DIM).pack(side=tk.LEFT, padx=(4, 0))

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

        self.diag_btn = tk.Button(
            btn_frame, text="Diagnostics", font=FONT_SMALL,
            bg=BG_SECONDARY, fg=FG_DIM, activebackground=BORDER, activeforeground=FG,
            relief=tk.FLAT, padx=8, pady=2, cursor="hand2",
            command=self._show_diagnostics,
        )
        self.diag_btn.pack(side=tk.LEFT, padx=(4, 0))

        self.bug_btn = tk.Button(
            btn_frame, text="Bug Report", font=FONT_SMALL,
            bg=BG_SECONDARY, fg="#f38ba8", activebackground=BORDER, activeforeground="#f38ba8",
            relief=tk.FLAT, padx=8, pady=2, cursor="hand2",
            command=self._show_bug_report,
        )
        self.bug_btn.pack(side=tk.LEFT, padx=(4, 0))

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
            apply_hunk=self.hunk_var.get(),
            apply_rbtree=self.rbtree_var.get(),
            apply_fcvar=self.fcvar_var.get(),
            apply_keyvalues=self.keyvalues_var.get(),
            apply_brushes=self.brushes_var.get(),
            apply_planes=self.planes_var.get(),
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

    def _show_diagnostics(self) -> None:
        self.log_widget.clear()
        self.log_widget.append("Collecting diagnostics...", "accent")

        def _worker():
            try:
                from core.diagnostics import collect_diagnostics, format_diagnostics
                info = collect_diagnostics(self.path_var.get().strip())
                report = format_diagnostics(info)
                self.root.after(0, lambda: self._show_diag_report(report))
            except Exception as import_exc:
                self.root.after(0, lambda: self.log_widget.append("ERROR: " + str(import_exc), "error"))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_diag_report(self, report: str) -> None:
        self.log_widget.clear()
        for line in report.split("\n"):
            if not line.strip():
                continue
            if line.startswith("==="):
                self.log_widget.append(line, "accent")
            elif line.startswith("  "):
                self.log_widget.append(line, "dim")
            elif "?" in line or "NOT FOUND" in line or "No" in line:
                self.log_widget.append(line, "warning")
            elif "Yes" in line or "Patches:" in line:
                self.log_widget.append(line, "success")
            else:
                self.log_widget.append(line, "info")
        self.log_widget.append("\nSelect all and copy (Ctrl+A, Ctrl+C) for bug reports.", "dim")

    def _show_bug_report(self) -> None:
        BugReportWindow(self.root, self.path_var.get().strip())

    def run(self) -> None:
        self.root.mainloop()
