<div align="center">

# 🎬 SFM Community Patcher v2.6

### *Engine stability, memory limits & Vulkan graphics for Source Filmmaker*

**Limina Flow** · **BedrockSFM**

<br>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![SFM](https://img.shields.io/badge/SFM-32--bit-1B2838?logo=steam&logoColor=white)](https://store.steampowered.com/app/1840/Source_Filmmaker/)

<br>

📘 [**English Guide**](instruction_eng.md) · 🇷🇺 [**Русское руководство**](instruction_ru.md)

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

## Key Features & Fixes

| Subsystem / Issue | Error Symptom | Target Binary |
|-------------------|---------------|---------------|
| **Hunk Memory** | `Engine hunk overflow!` | `bin\engine.dll` |
| **RBTree Index** | `CUtlRBTree overflow!` | `bin\engine.dll` |
| **Console Flags** | `FCVAR_CHEAT` command restrictions | `bin\engine.dll` |
| **KeyValues Pool** | `Out of keyvalue string space` | `bin\vstdlib.dll` |
| **Map Brushes** | `Map has too many brushes` | `bin\engine.dll` (8192 → 16384) |
| **Map Planes** | `Map has too many planes` | `bin\engine.dll` (65536 → 131072) |
| **Edicts** *(experimental)* | `ED_Alloc: no free edicts` | `step08` — **excluded** from default menu |
| **Graphics Chain** | ReShade + DXVK `d3d9.dll` conflict | `bin\ReShade.ini` → `[PROXY]` |

---

## Environment Requirements

- **OS:** Windows 10 or Windows 11 (64-bit host; SFM runs as **32-bit**)
- **Game:** [Source Filmmaker](https://store.steampowered.com/app/1840/Source_Filmmaker/) installed via **Steam**
- **Runtime:** [Python 3.x](https://www.python.org/downloads/) available on `PATH` (the `py` launcher in Command Prompt)
- **Graphics (optional but recommended):**
  - [DXVK](https://github.com/doitsujin/dxvk/releases) — **x32** build (`d3d9.dll` renamed to `d3d9_vlk.dll`)
  - [ReShade](https://reshade.me/) **6.7 or newer** — **32-bit**, Direct3D 9

---

## Repository Layout

Deploy the repository contents into your SFM **`game`** directory (alongside `sfm.exe`):

```text
SourceFilmmaker\game\
├── sfm.exe
├── patch_sfm.bat                 # Interactive patcher menu
├── setup_reshade_dxvk.bat        # ReShade [PROXY] → DXVK chain
├── instruction_eng.md            # Full English walkthrough
├── instruction_ru.md             # Полное руководство (RU)
├── README.md
├── LICENSE
└── sfm_patcher\
    ├── apply_all.py              # Run all patch steps
    ├── configure_reshade_dxvk.py # ReShade 6.7+ PROXY setup
    ├── step01_dxvk_loadlibrary.py
    ├── step02_hunk_overflow.py
    ├── step03_rbtree_overflow.py
    ├── step04_fcv_flags.py
    ├── step05_keyvalue_string_space.py
    ├── step06_map_brush_limit.py
    ├── step07_map_plane_limit.py
    ├── step08_edict_limit.py      # Manual only (not in patch_sfm menu 1)
    ├── lib\                       # Binary patch engine
    │   ├── binary_patch.py
    │   ├── patch_defs.py
    │   └── apply_patches.py
    └── tools\                     # Optional RE utilities (dev only)
```

---

## Quick Start Installation

1. **Extract** all repository files into `Steam\steamapps\common\SourceFilmmaker\game\` (next to `sfm.exe`).

2. **Install DXVK:** copy `d3d9.dll` from the DXVK **x32** package into `game\bin\` and **rename** it to **`d3d9_vlk.dll`**.

3. **Install ReShade:** run the ReShade installer targeting **`game\bin\dmxedit.exe`** (not `sfm.exe`) — API **Direct3D 9**, **32-bit**. Confirm **`bin\d3d9.dll`** exists (ReShade proxy).

4. **Close SFM**, then run **`patch_sfm.bat`** → option **1** to apply engine and KeyValues patches.

5. Run **`setup_reshade_dxvk.bat`** once to configure the ReShade **`[PROXY]`** chain to `d3d9_vlk.dll`.

6. **Launch Source Filmmaker from Steam** as you normally would. Verify DXVK in `game\sfm_d3d9.log` and ReShade hooks in `bin\ReShade.log`.

---

## CLI & Advanced Automation

```bash
cd /d "C:\Program Files (x86)\Steam\steamapps\common\SourceFilmmaker\game"

# Preview all patches without writing files
py -3 sfm_patcher\apply_all.py --dry-run --skip-dxvk

# Apply engine + vstdlib patches (skips legacy d3d9_vlk LoadLibrary patch)
py -3 sfm_patcher\apply_all.py --skip-dxvk

# Restore all backed-up DLLs from bin\backups\
py -3 sfm_patcher\apply_all.py --restore

# Individual steps
py -3 sfm_patcher\step02_hunk_overflow.py
py -3 sfm_patcher\step03_rbtree_overflow.py
py -3 sfm_patcher\step04_fcv_flags.py
py -3 sfm_patcher\step05_keyvalue_string_space.py
py -3 sfm_patcher\step06_map_brush_limit.py
py -3 sfm_patcher\step07_map_plane_limit.py
py -3 sfm_patcher\configure_reshade_dxvk.py
```

### `patch_sfm.bat` menu

| Key | Action |
|-----|--------|
| `1` | Apply engine patches (`--skip-dxvk --skip-edicts`) |
| `2` | Dry-run preview |
| `3` | Restore from `bin\backups\` |
| `5` | ReShade + DXVK setup only |
| `4` | Exit |

---

## ReShade 6.7+ & DXVK Proxy Mechanics

ReShade **6.7 and later** removed support for the environment variable **`RESHADE_MODULE_PATH_OVERRIDE`** and the legacy **`[INSTALL] ModulePath`** INI key. Hooking DXVK through the old workflow will silently fall back to **system `d3d9.dll`**, and ReShade effects will run without Vulkan translation.

This patcher configures the official **proxy library** chain instead:

```ini
[PROXY]
EnableProxyLibrary=1
ProxyLibrary=d3d9_vlk.dll
```

**Expected render path:**

```text
Steam → sfm.exe → LoadLibrary("d3d9.dll") → bin\d3d9.dll (ReShade)
                                      → bin\d3d9_vlk.dll (DXVK / Vulkan)
```

After a successful launch, **`bin\ReShade.log`** should contain a line similar to:

```text
Installing export hooks for '...\SourceFilmmaker\game\bin\d3d9_vlk.dll' ...
```

If you only see `C:\WINDOWS\system32\d3d9.dll`, re-run **`setup_reshade_dxvk.bat`** and confirm **`d3d9_vlk.dll`** is present in `bin\`.

---

## Rollback & Maintenance

| Goal | Procedure |
|------|-----------|
| **Undo patcher changes** | `patch_sfm.bat` → **3**, or `py -3 sfm_patcher\apply_all.py --restore` |
| **Restore vanilla Steam files** | Steam → SFM → Properties → **Verify integrity of game files** |
| **Remove graphics stack** | Delete `bin\d3d9.dll`, `bin\d3d9_vlk.dll`, `d3d9_dxvk.dll`, and ReShade presets/shaders as needed |
| **Remove PROXY only** | Delete the `[PROXY]` section from `bin\ReShade.ini` |

Backups created by the patcher live in **`bin\backups\`** and are **not** overwritten on subsequent runs.

---

## Post-Update Resilience

Steam updates may replace **`engine.dll`**, **`vstdlib.dll`**, or **`shaderapidx9.dll`**, invalidating signature-based patches.

1. Close SFM.
2. Run **`patch_sfm.bat`** → **2** (dry-run) and confirm all steps report planned changes.
3. If a step reports **signature mismatch**, wait for a patcher release matched to your build, or open a GitHub issue with:
   - SFM / Steam build date
   - Affected DLL file size (bytes)
   - Dry-run console output

Re-run **`setup_reshade_dxvk.bat`** after reinstalling ReShade, as updates may reset `ReShade.ini`.

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
