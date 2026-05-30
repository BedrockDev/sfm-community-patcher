# SFM Community Patcher — как устроен Source (кратко)

Это не официальная документация Valve, а практическая шпаргалка под **вашу** установку SFM.

## Графика: кто что грузит

```
sfm.exe
  └── engine.dll
        └── materialsystem.dll   ← материалы, текстуры, шейдеры (абстракция)
              └── shaderapidx9.dll   ← здесь Direct3D 9 и LoadLibrary("d3d9.dll")
```

- **materialsystem.dll** — уровень «какой API шейдеров», но **не** всегда содержит имя `d3d9.dll`.
- **shaderapidx9.dll** — реальная точка для DX9; в SFM 2025 строка `d3d9.dll` именно здесь.
- **ReShade** цепляется за `d3d9.dll` в папке игры; **DXVK** переименовываем в `d3d9_vlk.dll` и правим строку в `shaderapidx9.dll`.

## Память: Hunk vs CUtlRBTree

| Ошибка в ТЗ | Реальная строка в **вашей** SFM | Файл |
|-------------|------------------------------|------|
| `Engine Hunk Overflow` | `Engine hunk overflow!` | `bin/engine.dll` |
| `CUtlRBTree: overflow error` | `CUtlRBTree overflow!` | `bin/engine.dll` (в `sfm.exe` этой строки нет) |

Это **разные** лимиты; патч одного не лечит другой.

## Безопасность патчей

- Перед первой записью копия уходит в `bin\backups\имяфайла` (один раз).
- Старые `bin\*.bak` при первом запуске подхватываются в `backups\`.
- Размер PE не меняется.
- Строка `d3d9.dll` → `d3d9_vlk.dll` длиннее на 4 байта — расширяем только в нулевой паддинг.

## Быстрый старт (всё сразу)

```bat
cd /d "D:\SteamLibrary\steamapps\common\SourceFilmmaker\game"
patch_sfm.bat
```

Или вручную:

```bat
py -3 sfm_patcher\apply_all.py --dry-run
py -3 sfm_patcher\apply_all.py
py -3 sfm_patcher\apply_all.py --restore
```

## Шаги

| Шаг | Скрипт | Файл |
|-----|--------|------|
| 1 DXVK | `step01_dxvk_loadlibrary.py` | `shaderapidx9.dll` |
| 2 Hunk | `step02_hunk_overflow.py` | `engine.dll` |
| 3 RBTree | `step03_rbtree_overflow.py` | `engine.dll` |
| 4 ConVar | `step04_fcv_flags.py` | `engine.dll` (FCVAR_CHEAT) |

По умолчанию шаг 1 патчит **shaderapidx9.dll**. Флаг `--legacy-materialsystem` — опционально `materialsystem.dll`.
