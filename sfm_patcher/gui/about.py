# -*- coding: utf-8 -*-
"""
About window for SFM Community Patcher v3.0.
"""

from __future__ import annotations

import os
import random
import sys
import tkinter as tk
import webbrowser
from typing import Optional

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .styles import (
    ACCENT, BG, BORDER, FG, FG_DIM, FONT_LABEL, FONT_SMALL,
)

YOUTUBE_BEDROCK = "https://www.youtube.com/@bedrock_official"
YOUTUBE_STUDIO = "https://www.youtube.com/@liminaflowstudio"


def _get_assets_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_image(label: tk.Label, filename: str, max_width: int, max_height: int) -> bool:
    """Load image and attach directly to label to prevent GC."""
    if not HAS_PIL:
        return False
    assets_dir = _get_assets_dir()
    candidates = [
        os.path.join(assets_dir, filename),
    ]
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(sys._MEIPASS, filename))

    for path in candidates:
        if os.path.isfile(path):
            try:
                img = Image.open(path)
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label.config(image=photo)
                label.image = photo
                return True
            except Exception:
                pass
    return False


class AboutWindow:
    def __init__(self, parent: tk.Tk) -> None:
        self.win = tk.Toplevel(parent)
        self.win.title("About")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.geometry("400x500")

        self._build()

        self.win.update_idletasks()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        x = (self.win.winfo_screenwidth() // 2) - (w // 2)
        y = (self.win.winfo_screenheight() // 2) - (h // 2)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self) -> None:
        root = tk.Frame(self.win, bg=BG, padx=24, pady=20)
        root.pack(fill=tk.BOTH, expand=True)

        # Logos
        logos_frame = tk.Frame(root, bg=BG)
        logos_frame.pack(pady=(0, 12))

        studio_label = tk.Label(logos_frame, bg=BG, width=100, height=100)
        studio_label.pack(side=tk.LEFT, padx=12)
        _load_image(studio_label, "StudioLogo.jpg", 90, 90)

        bedrock_label = tk.Label(logos_frame, bg=BG, width=100, height=100)
        bedrock_label.pack(side=tk.LEFT, padx=12)
        _load_image(bedrock_label, "channel_profile.jpg", 90, 90)

        # Title
        tk.Label(
            root, text="SFM Community Patcher", font=("Segoe UI", 16, "bold"),
            bg=BG, fg=FG,
        ).pack(pady=(0, 2))
        tk.Label(
            root, text="Version 3.0", font=("Segoe UI", 11),
            bg=BG, fg=ACCENT,
        ).pack(pady=(0, 12))

        # Divider
        tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 12))

        # Copyright
        tk.Label(
            root, text="Copyright \u00a9 2026", font=FONT_LABEL,
            bg=BG, fg=FG_DIM,
        ).pack()
        tk.Label(
            root, text="BedrockSFM  &  Limina Flow", font=("Segoe UI", 11, "bold"),
            bg=BG, fg=FG,
        ).pack(pady=(2, 2))
        tk.Label(
            root, text="By creators, for creators.", font=FONT_SMALL,
            bg=BG, fg=FG_DIM,
        ).pack(pady=(0, 12))

        # Divider
        tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 12))

        # Links
        tk.Label(
            root, text="Official Channels:", font=FONT_LABEL,
            bg=BG, fg=FG_DIM,
        ).pack(anchor=tk.W, pady=(0, 4))

        link1 = tk.Label(
            root, text="\U0001f3ac  BedrockSFM", font=("Segoe UI", 10),
            bg=BG, fg=ACCENT, cursor="hand2",
        )
        link1.pack(anchor=tk.W, pady=2, padx=(16, 0))
        link1.bind("<Button-1>", lambda e: webbrowser.open(YOUTUBE_BEDROCK))
        link1.bind("<Enter>", lambda e: link1.config(fg="#89dceb"))
        link1.bind("<Leave>", lambda e: link1.config(fg=ACCENT))

        link2 = tk.Label(
            root, text="\U0001f3ac  Limina Flow Studio", font=("Segoe UI", 10),
            bg=BG, fg=ACCENT, cursor="hand2",
        )
        link2.pack(anchor=tk.W, pady=2, padx=(16, 0))
        link2.bind("<Button-1>", lambda e: webbrowser.open(YOUTUBE_STUDIO))
        link2.bind("<Enter>", lambda e: link2.config(fg="#89dceb"))
        link2.bind("<Leave>", lambda e: link2.config(fg=ACCENT))

        # Divider
        tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X, pady=(12, 12))

        # License
        tk.Label(
            root, text="Licensed under MIT License", font=FONT_SMALL,
            bg=BG, fg=FG_DIM,
        ).pack(pady=(0, 4))

        # Joke
        jokes = [
            "If this tool saved your scene from crashing \u2014 you're welcome.",
            "No DLLs were harmed in the making of this patcher.",
            "Powered by binary patching and an unreasonable amount of coffee.",
            "Engine hunk overflow? Not on my watch.",
            "Made with love, panic, and hex editors.",
            "This patcher runs on hopes, dreams, and unsigned int32.",
            "If you're reading this, the patches probably applied. Probably.",
            "I'm not saying I fixed all crashes, but I definitely blamed Valve.",
            "64-bit? No. Unlimited bit? Yes.",
            "CUtlRBTree? More like CUtlRBTryAgain.",
            "Warning: This patcher may cause sudden bursts of productivity.",
            "The only thing older than this engine is Gabe's chair.",
            "If it works, don't ask how. If it breaks, send screenshots.",
            "No Gaben was harmed in the making of this patch.",
            "Engine hunk overflow? I hunk it's fixed."
        ]
        tk.Label(
            root, text=random.choice(jokes), font=FONT_SMALL,
            bg=BG, fg=FG_DIM, wraplength=340, justify=tk.CENTER,
        ).pack(pady=(8, 0))
