<div align="center">

# SFM Community Patcher v3.2

### *Engine stability, memory limits & Vulkan graphics for Source Filmmaker*

**BedrockSFM** · **Limina Flow**

<br>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![SFM](https://img.shields.io/badge/SFM-32--bit-1B2838?logo=steam&logoColor=white)](https://store.steampowered.com/app/1840/Source_Filmmaker/)

<br>



</div>

---

> [!WARNING]
> **Disclaimer**
>
> This project is **not affiliated with, endorsed by, or supported by Valve Corporation**. All patches are applied as **local byte-level edits** to your own game installation — **use at your own risk**.
>
> - PE file sizes are **never modified** (patches only replace bytes in-place).
> - Original DLLs are backed up automatically on first run to **`bin\backups\`**.
> - You must own Source Filmmaker via Steam. Valve binaries are **not** distributed with this repository.

---

## What's New in v3.2

- **Single EXE** — no Python required, just download and run
- **GUI interface** — dark theme, one-click install
- **Auto-download** — DXVK and ReShade fetched automatically from GitHub
- **Auto-detect SFM** — finds your Steam library automatically
- **About window** — credits, links, and a joke

---

## Key Features & Fixes

| Subsystem / Issue | Error Symptom | Target Binary |
|-------------------|---------------|---------------|
| **Hunk Memory** | `Engine hunk overflow!` | `bin\engine.dll` |
| **RBTree Index** | `CUtlRBTree overflow!` | `bin\engine.dll` |
| **Console Flags** | `FCVAR_CHEAT` command restrictions | `bin\engine.dll` |
| **KeyValues Pool** | `Out of keyvalue string space` | `bin\vstdlib.dll` |
| **Map Brushes** | `Map has too many brushes` | `bin\engine.dll` (8192 → 16384) |
| **Map Planes** | `Map has too many planes` | `bin\engine.dll` (65536 → 131072) |
| **Edicts** *(experimental)* | `ED_Alloc: no free edicts` | `engine.dll` — **off by default** |
| **Graphics Chain** | ReShade + DXVK `d3d9.dll` conflict | `bin\ReShade.ini` → `[PROXY]` |

---

## Quick Start

1. Download **`SFM_Patcher_v3.exe`** from [Releases](../../releases).
2. Run it. The patcher will:
   - Find your SFM installation automatically
   - Download and install DXVK (Vulkan renderer)
   - Download and install ReShade (post-processing)
   - Configure the ReShade → DXVK proxy chain
   - Apply all engine patches
3. Launch Source Filmmaker from Steam.

That's it. One exe, one click.

---

## Requirements

- **OS:** Windows 10 or Windows 11 (64-bit host; SFM runs as **32-bit**)
- **Game:** [Source Filmmaker](https://store.steampowered.com/app/1840/Source_Filmmaker/) installed via **Steam**
- No Python, no manual DXVK/ReShade setup needed

---

## Command Line

```bash
SFM_Patcher_v3.exe --help          # Show options
SFM_Patcher_v3.exe --cli           # CLI mode
SFM_Patcher_vatcher_v3.exe --cli --dry-run   # Preview without changes
SFM_Patcher_v3.exe --cli --restore           # Restore from backups
```

---

## Troubleshooting

### Rendering broken / black screen

- **Cause:** DXVK incompatibility with your GPU or driver.
- **Fix:** Update your GPU drivers. If still broken, delete `bin\d3d9_vlk.dll` and `bin\d3d9_dxvk.dll` to disable DXVK. Patches will still work without Vulkan.

### SFM crashes on startup

- **Cause:** Patches applied to wrong DLL version, or SFM updated after patching.
- **Fix:** Click **Restore** in the patcher, or verify game files in Steam. Then re-patch.

### "Engine hunk overflow" still appears

- **Cause:** Patches not applied or SFM updated.
- **Fix:** Run the patcher again. If the error persists, check the **Diagnostics** output and report it.

### ReShade not loading

- **Cause:** `ReShade.ini` missing or proxy not configured.
- **Fix:** Run the patcher again, or manually add to `bin\ReShade.ini`:
  ```ini
  [PROXY]
  EnableProxyLibrary=1
  ProxyLibrary=d3d9_vlk.dll
  ```

### DXVK not loading

- **Cause:** `d3d9_vlk.dll` missing from `bin\`.
- **Fix:** Run the patcher again, or manually download DXVK x32 and copy `d3d9.dll` to `bin\d3d9_vlk.dll`.

### Patches say "no changes needed" but errors still happen

- **Cause:** Your SFM build has different byte signatures.
- **Fix:** Click **Diagnostics**, copy the output, and open a GitHub issue with the info.

### How to report a bug

1. Open the patcher, click **Diagnostics**
2. Click **Copy to Clipboard**
3. Paste the output in a [GitHub issue](../../issues/new)
4. Describe what happens (crash, rendering issue, error message)

---

## ReShade 6.7+ & DXVK Proxy Chain

This patcher configures the official **proxy library** chain:

```ini
[PROXY]
EnableProxyLibrary=1
ProxyLibrary=d3d9_vlk.dll
```

**Render path:**

```text
Steam → sfm.exe → d3d9.dll (ReShade) → d3d9_vlk.dll (DXVK / Vulkan)
```

---

## Rollback & Maintenance

| Goal | Procedure |
|------|-----------|
| **Undo patcher changes** | Click **Restore** in GUI, or `--cli --restore` |
| **Restore vanilla Steam files** | Steam → SFM → Properties → **Verify integrity of game files** |
| **Remove graphics stack** | Delete `bin\d3d9.dll`, `bin\d3d9_vlk.dll`, and ReShade presets/shaders |
| **Remove PROXY only** | Delete the `[PROXY]` section from `bin\ReShade.ini` |

Backups are saved to **`bin\backups\`** on first patch and never overwritten.

---

## Building from Source

```bash
pip install pyinstaller pillow
python build.py
```

Output: `dist\SFM_Patcher_v3.exe`

---

## Repository Structure

```
sfm_community_patcher/
├── SFM_Patcher_v3.exe              # Standalone build (in dist/)
├── sfm_patcher/
│   ├── __main__.py                 # Entry point
│   ├── core/
│   │   ├── sfm_detector.py         # Auto-find SFM in Steam
│   │   ├── downloader.py           # Download DXVK/ReShade
│   │   ├── reshade_installer.py    # Headless ReShade setup
│   │   └── setup.py                # Unified install process
│   ├── gui/
│   │   ├── app.py                  # Main window (tkinter)
│   │   ├── about.py                # About dialog
│   │   ├── log_widget.py           # Log output widget
│   │   └── styles.py               # Theme & colors
│   ├── lib/
│   │   ├── binary_patch.py         # Core patching engine
│   │   ├── patch_defs.py           # Signature definitions
│   │   └── apply_patches.py        # Patch applicator
│   ├── configure_reshade_dxvk.py   # ReShade INI config
│   └── step01-08_*.py              # Individual patch steps
├── build.py                        # PyInstaller build script
├── version_info.py                 # EXE version metadata
├── logotype.ico                    # App icon
├── StudioLogo.jpg                  # Limina Flow logo
├── channel_profile.jpg             # BedrockSFM avatar
├── instruction_eng.md
├── instruction_ru.md
├── LICENSE
└── README.md
```

---

## License

**MIT License**

Copyright (c) 2026 **BedrockSFM**, **Limina Flow**

See [LICENSE](LICENSE) for the full text.

Third-party components ([DXVK](https://github.com/doitsujin/dxvk), [ReShade](https://reshade.me/)) remain under their respective licenses. Source Filmmaker and the Source engine are trademarks of **Valve Corporation**.

---

<div align="center">

**Built for the SFM community · Patch responsibly · Back up before you ship**

</div>
