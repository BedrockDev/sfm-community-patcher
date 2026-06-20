# -*- coding: utf-8 -*-
"""
SFM Community Patcher v3.0 — Entry point.

Usage:
    python -m sfm_patcher          # Launch GUI
    python -m sfm_patcher --cli    # CLI mode (for PyInstaller)
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="SFM Community Patcher v3.0")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--bin-dir", default=None, help="Path to SFM bin directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--restore", action="store_true", help="Restore from backups")
    parser.add_argument("--install-dxvk", action="store_true", help="Install DXVK")
    parser.add_argument("--install-reshade", action="store_true", help="Install ReShade")
    args = parser.parse_args()

    if args.cli:
        from core.setup import SetupConfig, run_setup

        config = SetupConfig(
            game_dir=args.bin_dir or "",
            install_dxvk=args.install_dxvk or args.bin_dir is None,
            install_reshade=args.install_reshade or args.bin_dir is None,
            apply_patches=not args.restore,
            dry_run=args.dry_run,
        )
        result = run_setup(config)
        sys.exit(0 if result.success else 1)
    else:
        from gui.app import App
        app = App()
        app.run()


if __name__ == "__main__":
    main()
