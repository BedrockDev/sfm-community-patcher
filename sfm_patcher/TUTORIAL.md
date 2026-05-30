# SFM Community Patcher — руководство для туториала

Документ описывает, **что именно** меняет патчер, **зачем** это нужно и **как** установить всё с нуля (включая DXVK + ReShade).

---

## 1. Зачем это нужно

Source Filmmaker (движок Source 1) имеет жёсткие лимиты и ограничения, из‑за которых на тяжёлых сценах и картах часто вылетает:

| Проблема | Симптом |
|----------|---------|
| Мало Hunk-памяти | `Engine hunk overflow!` на больших BSP / картах |
| Лимит CUtlRBTree | `CUtlRBTree overflow!` при множестве моделей, костей, ключей |
| FCVAR_CHEAT | Часть консольных команд недоступна без «читов» |
| DXVK + ReShade | Оба хотят имя `d3d9.dll` — конфликт без разделения |

Патчер **не заменяет** файлы целиком: он делает **точечные байтовые правки** в ваших DLL с сохранением размера файла и резервной копией в `bin\backups\`.

---

## 2. Что патчится (сводка)

### Файлы

| Файл | Шаг | Что меняется |
|------|-----|----------------|
| `bin\shaderapidx9.dll` | 1 | Строка загрузки D3D9: `d3d9.dll` → `d3d9_vlk.dll` |
| `bin\engine.dll` | 2, 3, 4 | Лимиты Hunk, маска RBTree, проверка FCVAR_CHEAT |
| `bin\materialsystem.dll` | — | **Не патчится** (в SFM строки `d3d9.dll` там нет) |

### Шаг 1 — DXVK (shaderapidx9.dll)

**Суть:** движок при старте вызывает `LoadLibrary("d3d9.dll")`. Мы переименовываем цель в **`d3d9_vlk.dll`**, чтобы в `bin\` (или `game\`) свободным осталось имя **`d3d9.dll`** для ReShade.

- **Было (8 байт):** `d3d9.dll`  
- **Стало (12 байт):** `d3d9_vlk.dll` — длина растёт только за счёт **нулевого паддинга** после строки в PE (размер DLL не меняется).
- **Смещение (пример для типичной SFM):** `0x001463E4` в `shaderapidx9.dll` (1 безопасное вхождение из 2).
- Второе вхождение `d3d9.dll` в том же файле **не трогается** — после строки нет достаточного паддинга (иначе сломается таблица данных).

### Шаг 2 — Hunk overflow (engine.dll)

Ошибка в игре: **`Engine hunk overflow!`** (не «Engine Hunk Overflow» из старых гайдов).

Три правки:

1. **Потолок при расчёте hunk под карту**  
   `cmp eax, 512 MB` → `cmp eax, 2 GB`

2. **Стартовая инициализация hunk**  
   `push 32 MB` + `mov esi, 48 MB` → `push 256 MB` + `mov esi, 1 GB`

3. **Минимальный резерв**  
   `cmp esi, 40 MB` → `cmp esi, 256 MB`

### Шаг 3 — CUtlRBTree overflow (engine.dll)

Ошибка: **`CUtlRBTree overflow!`**

- **24 замены** одного шаблона в `engine.dll`:  
  `and ecx, 0xFFFF` → `and ecx, 0x7FFFFFFF`  
  (снимается 16-битный потолок ~65535 элементов в индексе дерева Valve).
- **`sfm.exe` не патчится** — в нём нет этой строки ошибки; логика RBTree для сцены идёт через `engine.dll`.

### Шаг 4 — ConVar / FCVAR_CHEAT (engine.dll)

- **1 правка:** обход проверки флага **`FCVAR_CHEAT`** (`0x4000`) при доступе к ConVar.  
- Отдельного снятия **`FCVAR_DEVELOPMENTONLY`** в этой сборке не найдено — при обновлении Steam паттерн может отличаться.

**Важно:** для части команд по-прежнему может понадобиться в консоли: `sv_cheats 1`.

---

## 3. Подготовка: DXVK + ReShade (до патча)

### 3.1. ReShade + DXVK вместе (рекомендуется)

Старый вариант «патч на `d3d9_vlk.dll`» **обходит ReShade** — движок грузит DXVK напрямую, эффекты ReShade не работают.

Правильная цепочка (официальный механизм ReShade, с ReShade 4.5+):

```
SFM -> LoadLibrary("d3d9.dll") -> bin\d3d9.dll (ReShade)
     -> RESHADE_MODULE_PATH_OVERRIDE\bin\dxvk_backend\d3d9.dll (DXVK)
```

**Один раз** (после патчей engine и установки DXVK/ReShade):

```bat
setup_reshade_dxvk.bat
```

или `patch_sfm.bat` → пункт **5**.

Скрипт:
- возвращает в `shaderapidx9.dll` строку **`d3d9.dll`** (откат шага 1);
- копирует DXVK в `bin\dxvk_backend\d3d9.dll`;
- включает ReShade как `bin\d3d9.dll`.

**Запуск из Steam** — `setup_reshade_dxvk.bat` прописывает в `bin\ReShade.ini` (ReShade **6.7+**):

```ini
[PROXY]
EnableProxyLibrary=1
ProxyLibrary=d3d9_vlk.dll
```

Старые `RESHADE_MODULE_PATH_OVERRIDE` и `[INSTALL] ModulePath` в 6.7 **не работают** — их убрали.

Проверка:
- `bin\ReShade.log` — ReShade инициализировался;
- `game\sfm_d3d9.log` — строка `DXVK: v2.x`, Vulkan, ваша видеокарта.

### 3.1a. Схема файлов

```
game\bin\
├── d3d9.dll              ← ReShade (прокси)
├── d3d9_vlk.dll          ← копия DXVK (источник для backend)
├── dxvk_backend\
│   └── d3d9.dll          ← DXVK для ReShade (не трогать вручную)
└── ReShade.ini / пресеты ...
```

### 3.2. Установка DXVK

1. Скачайте [DXVK](https://github.com/doitsujin/dxvk/releases) (для 32-bit игр — **x32** / `dxvk-*-x32.zip`).
2. Из архива возьмите **`d3d9.dll`** (из папки `x32` или `system32` внутри релиза).
3. Скопируйте в `SourceFilmmaker\game\bin\`.
4. **Переименуйте** копию в **`d3d9_vlk.dll`**.

> Не удаляйте оригинальные DLL Steam — патчер правит копии в `bin\`, а чистые файлы хранит в `bin\backups\`.

### 3.3. Установка ReShade

1. Установите ReShade для **32-bit**, укажите **`bin\dmxedit.exe`** (не `sfm.exe` — иначе рендер/вьюпорт без ReShade).
2. Выберите API **Direct3D 9**.
3. Убедитесь, что в **`game\bin\`** появился **`d3d9.dll`** от ReShade.

### 3.4. Порядок действий

1. Положить **`d3d9_vlk.dll`** (DXVK) в `bin\`.
2. Установить ReShade на **`bin\dmxedit.exe`** → **`d3d9.dll`** в `bin\`.
3. Запустить **патчер** (шаги 2–4 в `engine.dll`; шаг 1 для DXVK+ReShade **не обязателен**).
4. Запустить **`setup_reshade_dxvk.bat`** (цепочка ReShade → DXVK).
5. Запускать SFM **из Steam** (как обычно).

---

## 4. Установка патчера

### Требования

- Windows, установленный **Source Filmmaker** (Steam).
- **Python 3** в PATH (команда `py` в терминале).

### Состав в папке `game\`

```
game\
├── sfm.exe
├── patch_sfm.bat          ← меню одним кликом
└── sfm_patcher\
    ├── apply_all.py       ← все шаги подряд
    ├── step01_dxvk_loadlibrary.py
    ├── step02_hunk_overflow.py
    ├── step03_rbtree_overflow.py
    ├── step04_fcv_flags.py
    └── TUTORIAL.md        ← этот файл
```

---

## 5. Запуск патчера

### Вариант A — `patch_sfm.bat` (для видео)

1. **Закройте SFM** (проверка в bat: если `sfm.exe` запущен — предупреждение).
2. Откройте папку `SourceFilmmaker\game\`.
3. Дважды щёлкните **`patch_sfm.bat`**.
4. Меню:
   - **1** — применить все патчи;
   - **2** — dry-run (только показать, что будет изменено, **без записи**);
   - **3** — восстановить оригиналы из `bin\backups\`;
   - **4** — выход.

### Вариант B — командная строка

```bat
cd /d "D:\SteamLibrary\steamapps\common\SourceFilmmaker\game"

REM Сначала посмотреть план (безопасно)
py -3 sfm_patcher\apply_all.py --dry-run

REM Применить всё
py -3 sfm_patcher\apply_all.py

REM Откат
py -3 sfm_patcher\apply_all.py --restore
```

Отдельные шаги:

```bat
py -3 sfm_patcher\step01_dxvk_loadlibrary.py
py -3 sfm_patcher\step02_hunk_overflow.py
py -3 sfm_patcher\step03_rbtree_overflow.py
py -3 sfm_patcher\step04_fcv_flags.py
```

---

## 6. Резервные копии

| Когда | Что происходит |
|-------|----------------|
| Первый патч файла | Создаётся `bin\backups\имя.dll` (копия **до** правок) |
| Повторный патч | `backups\` **не перезаписывается** |
| Dry-run | Папка `backups\` **не создаётся** |
| Старые `*.bak` в `bin\` | При первом запуске **копируются** в `backups\` |

Пример после патча:

```
bin\
  engine.dll              ← пропатченный
  shaderapidx9.dll        ← пропатченный
  d3d9_vlk.dll            ← DXVK (вы положили сами)
  d3d9.dll                ← ReShade
  backups\
    engine.dll            ← оригинал Steam
    shaderapidx9.dll      ← оригинал Steam
```

**Откат:** `patch_sfm.bat` → пункт 3, или `apply_all.py --restore`.

**Восстановление через Steam:** «Проверить целостность» также вернёт чистые DLL (если не отключено для SFM).

---

## 7. Проверка после установки

1. Запустить SFM, загрузить тяжёлую сцену / карту.
2. **DXVK:** в `game\` может появиться `sfm_d3d9.log` или лог DXVK; в оверлее (если включён) видна версия DXVK.
3. **ReShade:** клавиша Home (по умолчанию) — открывается меню ReShade.
4. **Hunk / RBTree:** сцены, которые раньше падали с `overflow`, должны грузиться дольше/стабильнее (не гарантия бесконечной памяти — лимиты **увеличены**, не сняты полностью).
5. **Консоль:** `~` → попробовать ранее недоступные `mat_*` / `r_*` (при необходимости `sv_cheats 1`).

---

## 8. Частые вопросы

**Патч сломается после обновления Steam?**  
Да, если Valve заменит `engine.dll` / `shaderapidx9.dll`. Нужен новый dry-run и, возможно, обновление сигнатур в `patch_defs.py`.

**Можно только DXVK без engine-патчей?**  
Да: `py -3 sfm_patcher\step01_dxvk_loadlibrary.py` или `apply_all.py` после добавления флага `--skip-engine` (если добавите в скрипт). Сейчас `apply_all` гоняет все 4 шага.

**Почему не materialsystem.dll?**  
В актуальной SFM загрузка `d3d9.dll` идёт из **shaderapidx9.dll**. `materialsystem.dll` только управляет материалами.

**Безопасно ли для VAC?**  
SFM не использует VAC как CS2; это модификация локальных DLL. Риск бана минимален, но официально это не поддерживается Valve.

**Multiplayer / Team Fortress в той же папке?**  
Патчится общий `game\bin\` SFM — не запускайте соседние Source-игры из той же установки без отката, если делите `bin\`.

---

## 9. Краткий чеклист для описания видео

1. [ ] Python 3 установлен  
2. [ ] DXVK: `bin\d3d9_vlk.dll`  
3. [ ] ReShade: установка на `bin\dmxedit.exe`, файл `bin\d3d9.dll`  
4. [ ] SFM закрыт  
5. [ ] `patch_sfm.bat` → 2 (dry-run) → 1 (применить)  
6. [ ] Проверка: `bin\backups\` на месте  
7. [ ] Запуск SFM, тест сцены  

---

*Версия документа: под сборку SFM с `engine.dll` ~4.6 MB (2025). Смещения могут отличаться после обновления.*
