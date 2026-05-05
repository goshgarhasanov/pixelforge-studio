<div align="center">

# PixelForge Studio
### Professional Image Conversion · Resizing · Compression Suite

> **Build Specification & Master Prompt — v2.0**
> _For a Senior Python Desktop Engineer (15–20 yrs experience)_

</div>

---

## 0. Role Briefing for the AI Builder

You are a **Principal-level Python Desktop Application Engineer** with 15–20 years of professional experience. Your portfolio includes commercial apps shipped to millions of users on Windows, macOS, and Linux. You write code that is:

- **Idiomatic** — Pythonic, PEP-8/PEP-484 clean, type-annotated end-to-end.
- **Defensive** — handles edge cases, broken images, locked files, OOM, Unicode paths.
- **Performant** — multithreaded I/O, lazy loading, GPU-aware (where it makes sense).
- **Beautiful** — pixel-perfect UI, consistent spacing, vibrant but tasteful color system.
- **Maintainable** — small modules, dependency injection, no hidden globals.
- **Tested** — pytest with fixtures, ≥ 85% coverage on `core/`.
- **Shipped** — packaged as a one-file `.exe` via PyInstaller, signed-ready, with auto-update hook.

Treat this document as the **Product Requirements Document (PRD) + Engineering Brief**. Build incrementally, commit conventionally, and ship a polished v1.0.

---

## 1. Product Identity

| Attribute | Value |
| --- | --- |
| **Product name** | **PixelForge Studio** |
| **Tagline** | _"Forge every pixel. Convert. Resize. Compress."_ |
| **Internal codename** | `pixelforge` |
| **Repository** | `pixelforge-studio` |
| **Bundle ID** | `com.pixelforge.studio` |
| **License** | MIT |
| **Primary platform** | Windows 11 (.exe via PyInstaller) — also runs on macOS / Linux |

### 1.1 Alternative names (in case of conflict)

`Chromatica Pro` · `Spectrum Studio` · `PixelAlchemy` · `Pixly Pro` · `ImageForge` · `Compressly Studio`

### 1.2 Brand voice

Confident · Technical · Friendly · Zero corporate fluff. Microcopy speaks like a senior engineer talking to a peer ("Drop images here. We'll handle the rest.").

### 1.3 Language — **NATIVE AZERBAIJANI (az-Latn-AZ)**

**The entire application UI ships in Azerbaijani as the primary language.**

- All visible strings (buttons, labels, menus, tooltips, toasts, dialogs, status, errors) **must be in Azərbaycan dili**, written with correct grammar (`ı`, `ə`, `ö`, `ü`, `ş`, `ç`, `ğ`).
- All Python **code comments and docstrings must be in Azərbaycan dili** with grammatically correct sentences.
- Variable / function / class names stay in English (PEP 8) — only natural-language strings and comments are AZ.
- Log messages are in Azerbaijani too.
- Commit messages stay in English (Conventional Commits).
- README.md ships in Azerbaijani primarily.
- Use proper AZ UX terminology: Çevir, Ölçü dəyişdir, Sıxışdır, Toplu, Növbə, Tənzimləmələr, Çıxış qovluğu, Sürüklə və burax, Başla, Ləğv et, Dayandır, Davam et, Tamamlandı, Xəta, Xəbərdarlıq, Keyfiyyət, Hədəf ölçü, Qeydlər, Resept, Su nişanı.

> Grammar gate: re-read every string. If it sounds like Google Translate, rewrite it.

---

## 2. Mission & Scope

Build a **professional desktop GUI application** that does **three jobs world-class well**:

1. **Convert** images across the full format matrix (JPG, PNG, WEBP, GIF, BMP, TIFF, ICO, HEIC-read).
2. **Resize** by dimensions, percentage, presets, or smart auto-fit.
3. **Compress** to a target file size (default ≤ 200 KB) using a deterministic binary-search quality algorithm with optional codec swaps.

…wrapped in a **vibrant, modern, batch-friendly desktop experience** that ranks alongside FastStone, XnConvert, Caesium, and Squoosh — but with the polish of a 2026 product.

---

## 3. Feature Catalogue (Deep)

> Inspired by the best of **XnConvert** (500+ formats, 80+ actions), **FastStone Photo Resizer** (batch convert/rename/watermark), **Caesium** (target-size compression), **Squoosh** (codec comparison, MozJPEG/WebP/AVIF), **TinyPNG** (intelligent lossy), **ImageOptim** (multi-tool chaining), and **PowerToys Image Resizer** (right-click integration).

### 3.1 Core — Conversion

- Full **N×N conversion matrix** between: **JPG, PNG, WEBP, GIF, BMP, TIFF, ICO**, plus **HEIC/HEIF read-only** via `pillow-heif`.
- Smart handling:
  - **Alpha → no-alpha** → composite over user-chosen background (white default), with live preview.
  - **Animated GIF** → preserved when target supports animation (GIF/WEBP); otherwise frame 1 with warning.
  - **ICO output** → multi-resolution (16/32/48/64/128/256).
  - **Color profile** preservation (sRGB / Display P3 / Adobe RGB).
  - **EXIF** auto-rotate before processing; configurable strip-on-export (default: strip GPS, keep camera info).
- Per-format encoder controls: JPEG quality + chroma subsampling, PNG compression level + palette mode, WEBP method/quality/lossless.

### 3.2 Core — Resize

- Modes: **Pixels (W×H)**, **Percentage**, **Long edge**, **Short edge**, **Megapixels cap**, **Fit/Fill/Stretch**, **Smart crop** (face/focal-point aware via `mediapipe` — optional dependency).
- Lock aspect ratio toggle.
- **Resampling filters**: Lanczos (default), Bicubic, Bilinear, Nearest — selectable per job.
- **Upscale guard**: refuse to upscale beyond 2× without explicit confirmation.
- Built-in **preset library** (editable):
  - 📱 Instagram Post (1080×1080), Story (1080×1920), Reel cover.
  - 🐦 Twitter/X header (1500×500), post (1200×675).
  - 💼 LinkedIn banner (1584×396), profile (400×400).
  - 📺 YouTube thumbnail (1280×720).
  - 🌐 Web hero (1920×1080), thumbnail (320×180).
  - 📧 Email-safe (≤ 1 MB, max 1600px).
  - 🖼️ Wallpaper 4K / 1440p / 1080p.
  - 📄 Passport photo (35×45 mm @ 300 DPI).
  - 🔖 Favicon set (16/32/48/180/192/512).

### 3.3 Core — Compression (the killer feature)

- **Target-size mode**: user picks an upper bound in KB (default 200). The engine binary-searches JPEG/WEBP quality → if floor reached, progressively downscales (95% steps) until met or 320 px floor.
- **Codec battle mode** (Squoosh-style): show side-by-side preview of MozJPEG vs WebP vs PNG-quant vs AVIF (if `pillow-avif-plugin` present) with size + quality readout.
- **Lossless mode**: `oxipng`-style optimization for PNG, `cwebp -lossless` for WEBP.
- **Per-channel quality tuning** for power users (advanced panel).
- **Original preservation**: never overwrite source unless user explicitly enables _"Replace originals"_.

### 3.4 Batch & Automation

- **Drag & drop** (files, folders, mixed) — recursive folder scan with depth control.
- **Watch folder mode**: auto-process new files dropped into a directory.
- **Parallel workers** (configurable, defaults to `os.cpu_count() // 2`).
- **Per-file progress + global progress + ETA**.
- **Pause / Resume / Cancel** per job and global.
- **Action chains** (XnConvert-style): user defines a pipeline `[Rotate → Resize → Watermark → Convert → Compress]` and saves as a **Recipe** (JSON).
- **Drag-to-reorder** chain steps.
- **Recipes** are shareable `.pfrecipe` files (JSON, versioned).

### 3.5 Editing actions (chainable)

| Category | Actions |
| --- | --- |
| Geometry | Rotate (90°, free angle), Flip H/V, Crop (rect, ratio, smart), Auto-deskew |
| Tone | Brightness, Contrast, Saturation, Hue, Gamma, Auto-levels, Auto-WB |
| Effects | Sharpen (unsharp mask), Blur (Gaussian), Noise reduction, Vignette |
| Annotation | Text watermark (font/size/color/opacity/position), Image watermark (PNG/SVG, tiled or anchored), Border, Frame |
| Metadata | Strip EXIF / GPS / IPTC, Rename via tokens (`{name}_{w}x{h}_{date}`), Set timestamp |
| Color | Convert to grayscale / sepia / B&W, Posterize, Color profile assign/convert |

### 3.6 Power features

- **Right-click Explorer integration** (Windows): "Open with PixelForge", "Compress to 200 KB here".
- **Command-line mode**: `pixelforge --input ./pics --recipe web-hero.pfrecipe --target 200`.
- **Drag-out**: drag processed files from the queue back to Explorer.
- **Side-by-side preview** with split slider (before / after) and zoom 25–400%.
- **Histogram** panel (RGB + luminance).
- **Pixel inspector** (hex color + RGB + EXIF popover).
- **Undo stack** for queue edits (not destructive — sources never touched).
- **Crash-safe**: queue + recipes auto-saved every 5 s to `~/.pixelforge/state.json`.
- **Auto-update check** on launch (semver, GitHub Releases API).
- **Telemetry** strictly opt-in, anonymous, opt-out by default.
- **i18n ready** — string tables in `i18n/{lang}.json`, ship with English + Türkçe + Azərbaycanca.

---

## 4. Visual Design System

### 4.1 Brand colors (vibrant, high-energy)

```
PRIMARY GRADIENT (for hero, CTA, logo)
  Indigo  #6366F1  →  Fuchsia #D946EF  →  Amber  #F59E0B

ACCENT SET
  Electric Cyan      #06B6D4   (info / links)
  Lime Green         #84CC16   (success)
  Hot Coral          #F43F5E   (error / destructive)
  Sunflower          #FACC15   (warning)
  Royal Violet       #8B5CF6   (highlights)

NEUTRAL — DARK MODE (default)
  bg-deepest         #0B0B12
  bg-base            #12121A
  bg-elevated        #1B1B26
  bg-overlay         #25253A
  border-subtle      #2D2D45
  text-primary       #F4F4F8
  text-secondary     #A8A8C0
  text-muted         #6B6B8A

NEUTRAL — LIGHT MODE
  bg-base            #FAFAFC
  bg-elevated        #FFFFFF
  bg-overlay         #F1F1F7
  border-subtle      #E5E5EE
  text-primary       #0B0B12
  text-secondary     #52526B
```

> **Use color with intent.** Primary gradient for the hero band, logo, and the START button only. Status colors only on badges. Never paint flat backgrounds with brand colors — neutrals carry the layout.

### 4.2 Typography

- **Display** — `Inter` 700, fallback Segoe UI / SF Pro / system-ui.
- **Body** — `Inter` 400 / 500.
- **Mono** (logs, hex values) — `JetBrains Mono` 400.
- Sizes: 28 / 22 / 18 / 15 / 13 / 12 (px). Line-height 1.45.

### 4.3 Iconography

- Use **Lucide** icons (open-source, MIT) bundled as PNG @ 1x/2x — already drawn, no Unicode fallbacks.
- Icon size: 16 px in lists, 20 px in toolbar, 24 px in panel headers, 48 px in empty states.
- Stroke 1.75, rounded caps. Tint with `text-secondary` by default; `text-primary` on hover; brand color when active.
- Required icons: `image`, `image-plus`, `folder-open`, `download`, `play`, `pause`, `x-circle`, `check-circle-2`, `alert-triangle`, `settings-2`, `sun`, `moon`, `monitor`, `wand-sparkles`, `crop`, `flip-horizontal`, `rotate-cw`, `droplet`, `palette`, `gauge`, `zap`, `layers-3`, `history`, `trash-2`, `external-link`.

### 4.4 Logo

Build a **vector logo** (SVG → PNG/ICO) in `assets/logo/`:

- **Mark**: a stylized **anvil + pixel grid hybrid** — three pixel squares stacked into an anvil silhouette, the topmost pixel emitting a small spark. Filled with the **primary gradient** (Indigo → Fuchsia → Amber).
- **Wordmark**: `PixelForge` in Inter 800, letter-spacing −0.02em; `Studio` underneath in 500, tracked +0.10em, in `text-secondary`.
- Variants needed:
  - `logo-full.svg` (mark + wordmark, horizontal)
  - `logo-stacked.svg` (mark above wordmark)
  - `logo-mark.svg` (mark only, square)
  - `logo-mono-light.svg` / `logo-mono-dark.svg`
  - `icon.ico` (multi-res 16/32/48/64/128/256) for the .exe
  - `icon.png` 1024×1024 for store listings
- Generate via `scripts/build_logo.py` using `cairosvg` or hand-author the SVG; commit both source and rasterized outputs.

### 4.5 Layout (single window, 1280×800 default, min 1024×680)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ▓▓▓▓ PixelForge Studio                          🌙  ⚙   👤  ❓  ─ □ ✕   │ ← Title bar (custom, gradient strip)
├────────────────────────────────────────────────────────────────────────────┤
│ ┌─ Sidebar ─┐  ┌──────────── Main Workspace ─────────────┐ ┌─ Inspector ─┐│
│ │           │  │                                          │ │             ││
│ │ 🏠 Home   │  │  ╔══════════════════════════════════╗   │ │  Format     ││
│ │ 🪄 Convert│  │  ║      Drag & drop your images     ║   │ │  [JPG  ▼]  ││
│ │ 📐 Resize │  │  ║         or click to browse       ║   │ │             ││
│ │ 🗜 Compress│ │  ║   JPG · PNG · WEBP · GIF · HEIC  ║   │ │  Resize     ││
│ │ 📚 Recipes│  │  ╚══════════════════════════════════╝   │ │  ⦿ Pixels   ││
│ │ 🔍 Inspect│  │                                          │ │  ○ Percent  ││
│ │ ─────────  │  │  Queue (4)  ⏵ Start  ⏸ Pause  ✕ Clear  │ │  ○ Preset   ││
│ │ 📊 Stats  │  │  ┌────────────────────────────────────┐ │ │             ││
│ │ 📜 Logs   │  │  │ 🖼  hero.png    4.8 MB → … (queue) │ │ │  Target KB  ││
│ │ ⚙  Settings│ │  │ 🖼  banner.jpg  2.1 MB → 198 KB ✓  │ │ │  [  200  ⬍] ││
│ │           │  │  │ 🖼  team.heic   3.7 MB → … (work)  │ │ │             ││
│ │ ─────────  │  │  │ 🖼  logo.gif   620 KB → … (queue) │ │ │  Output     ││
│ │ 💎 Pro Tips│ │  └────────────────────────────────────┘ │ │  [./output] ││
│ └───────────┘  │  ▓▓▓▓▓▓▓▓▓▓░░░  72%   ETA 00:00:14    │ │             ││
│                │  ┌─── Preview (split) ─────────────┐   │ │ [▶ FORGE]  ││
│                │  │  before │ after                  │   │ │             ││
│                │  └─────────────────────────────────┘   │ │ Saved: 8.4MB││
│                └──────────────────────────────────────────┘ └─────────────┘│
├────────────────────────────────────────────────────────────────────────────┤
│ ● Ready  ·  4 files  ·  CPU 18%  ·  RAM 142 MB  ·  v1.0.0  ·  💾 ./output│ ← Status bar
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.6 Motion & micro-interactions

- 150 ms ease-out for hover, 220 ms ease-in-out for panel transitions.
- Drop zone glows with the primary gradient on hover-with-files.
- Queue rows shimmer (subtle gradient sweep) while processing.
- Confetti burst (lightweight, < 30 frames) when a batch completes — toggleable in Settings.
- Use **`pyautogui`-free** motion (pure tk `after()` tweens or `tkinter.ttk` styles).

### 4.7 Accessibility

- All controls keyboard-reachable; visible focus ring (2 px Indigo).
- Tooltips on every icon-only button.
- Color-blind-safe status badges (icon + color, never color alone).
- Respect OS scaling (HighDPI on Windows + macOS).
- Min contrast 4.5:1 for body text.

---

## 5. Tech Stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language | **Python 3.11+** | Pattern matching, exception groups |
| GUI | **CustomTkinter 5.x** | Modern dark/light theming, HighDPI |
| Drag & drop | `tkinterdnd2` | Native OS drop targets |
| Image core | **Pillow 10+** | Industry standard |
| HEIC | `pillow-heif` | Read-only |
| AVIF (optional) | `pillow-avif-plugin` | Codec battle mode |
| Smart crop | `mediapipe` (optional) | Lazy-imported; degrades gracefully |
| Compression | Pillow + `mozjpeg-lossless-optimization` (opt) | |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` + `queue` | UI thread-safe via `widget.after()` |
| Config | `pydantic-settings` | Persisted to `~/.pixelforge/config.toml` |
| Logging | stdlib `logging` + `RichHandler` (opt) + `RotatingFileHandler` | |
| Tests | `pytest`, `pytest-cov`, `Pillow` fixtures | |
| Lint | **ruff**, **black**, **mypy --strict** | Zero-warning policy |
| Packaging | **PyInstaller** (one-file + one-folder) | Windows .exe with icon |
| Installer | **Inno Setup** (Windows) | Optional, post-v1 |
| CI | GitHub Actions | lint + test (3.11/3.12, win+ubuntu) + release |

---

## 6. Repository Structure

```
pixelforge-studio/
├── README.md                       ← rich, with hero GIF
├── LICENSE                         ← MIT
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── pyproject.toml                  ← ruff, black, mypy, pytest, build
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  ← lint + test
│   │   ├── release.yml             ← PyInstaller build on tag
│   │   └── codeql.yml              ← security scan
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── assets/
│   ├── logo/
│   │   ├── logo-full.svg
│   │   ├── logo-stacked.svg
│   │   ├── logo-mark.svg
│   │   ├── logo-mono-light.svg
│   │   ├── logo-mono-dark.svg
│   │   ├── icon.ico
│   │   └── icon.png                ← 1024×1024
│   ├── icons/                      ← Lucide PNG bundle
│   ├── screenshots/
│   │   ├── hero.png
│   │   ├── batch.png
│   │   ├── compression.png
│   │   └── demo.gif
│   └── fonts/                      ← Inter, JetBrains Mono (OFL)
├── i18n/
│   ├── en.json
│   ├── tr.json
│   └── az.json
├── recipes/                        ← shipped recipe library
│   ├── web-hero.pfrecipe
│   ├── instagram-post.pfrecipe
│   └── email-safe.pfrecipe
├── scripts/
│   ├── build_logo.py               ← SVG → PNG/ICO
│   ├── make_release.py             ← PyInstaller wrapper
│   └── gen_screenshots.py
├── src/
│   └── pixelforge/
│       ├── __init__.py             ← __version__
│       ├── __main__.py             ← `python -m pixelforge`
│       ├── app.py                  ← bootstrap, DI, lifecycle
│       ├── cli.py                  ← argparse entrypoint
│       ├── config.py               ← pydantic-settings
│       ├── logger.py               ← rotating + in-app queue
│       ├── i18n.py                 ← translation loader
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py           ← Job, Recipe, Result, Preset
│       │   ├── converter.py        ← format conversion
│       │   ├── resizer.py
│       │   ├── compressor.py       ← target-size algorithm
│       │   ├── effects.py          ← rotate/flip/crop/watermark/etc.
│       │   ├── pipeline.py         ← chain executor
│       │   ├── recipes.py          ← .pfrecipe load/save/validate
│       │   ├── presets.py          ← built-in preset library
│       │   └── codecs.py           ← codec battle (mozjpeg/webp/avif)
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   ├── theme.py            ← color tokens, fonts, spacing
│       │   ├── icons.py            ← icon loader / cache
│       │   ├── widgets/
│       │   │   ├── titlebar.py
│       │   │   ├── sidebar.py
│       │   │   ├── drop_zone.py
│       │   │   ├── file_queue.py
│       │   │   ├── inspector.py
│       │   │   ├── settings_panel.py
│       │   │   ├── preview_split.py
│       │   │   ├── histogram.py
│       │   │   ├── progress.py
│       │   │   ├── log_viewer.py
│       │   │   ├── status_bar.py
│       │   │   ├── recipe_builder.py
│       │   │   ├── codec_battle.py
│       │   │   ├── toast.py
│       │   │   └── confetti.py
│       │   └── pages/
│       │       ├── home.py
│       │       ├── convert.py
│       │       ├── resize.py
│       │       ├── compress.py
│       │       ├── recipes.py
│       │       ├── stats.py
│       │       ├── logs.py
│       │       └── settings.py
│       ├── workers/
│       │   ├── __init__.py
│       │   ├── pool.py             ← ThreadPoolExecutor wrapper
│       │   ├── batch_worker.py
│       │   └── watch_folder.py
│       └── utils/
│           ├── __init__.py
│           ├── paths.py
│           ├── formats.py
│           ├── humanize.py
│           ├── exif.py
│           ├── colorprofile.py
│           ├── platform.py         ← shell integration helpers
│           └── update_checker.py
├── tests/
│   ├── conftest.py
│   ├── fixtures/                   ← sample images (small, real)
│   ├── unit/
│   │   ├── test_compressor.py      ← target-size correctness
│   │   ├── test_converter.py       ← matrix coverage
│   │   ├── test_resizer.py
│   │   ├── test_effects.py
│   │   ├── test_pipeline.py
│   │   ├── test_recipes.py
│   │   └── test_codecs.py
│   ├── integration/
│   │   ├── test_batch.py
│   │   └── test_cli.py
│   └── ui/
│       └── test_smoke.py           ← launch + close cleanly
├── docs/
│   ├── architecture.md             ← mermaid diagrams
│   ├── recipes.md
│   ├── compression-algorithm.md
│   └── packaging.md
├── output/                         ← .gitignore
└── logs/                           ← .gitignore
```

---

## 7. Core Algorithm — Target-Size Compression

`src/pixelforge/core/compressor.py`:

```python
def compress_to_target(
    image: Image.Image,
    target_kb: int = 200,
    fmt: Literal["JPEG", "WEBP", "PNG"] = "JPEG",
    *,
    min_quality: int = 35,
    max_quality: int = 95,
    min_short_edge: int = 320,
    downscale_step: float = 0.95,
    tolerance: float = 1.02,
) -> tuple[bytes, CompressionReport]:
    """
    Encode `image` to bytes that are <= target_kb * 1024 * tolerance.

    Strategy:
      1. Auto-rotate via EXIF, ensure RGB(A) mode appropriate for `fmt`.
      2. Binary-search quality in [min_quality, max_quality] (≤ 8 iters).
      3. If still oversize at min_quality, downscale by `downscale_step`
         and retry — until short-edge would drop below `min_short_edge`.
      4. Return bytes + a report (final quality, dims, iterations, bytes).

    Deterministic. Bounded. Pure (no I/O). Fully unit-tested.
    """
```

Tests must prove: every fixture image lands ≤ `target_kb * 1.02`; final `quality >= min_quality` whenever feasible; ≤ 8 quality iterations; no upscale ever; degrades gracefully when target is impossible (returns smallest achievable + warning in report).

---

## 8. Logging — Production-Grade

`src/pixelforge/logger.py`:

- Root logger configured once at app start.
- **Console handler**: INFO+, colorized via `RichHandler` if available, plain otherwise.
- **File handler**: `logs/pixelforge.log`, `RotatingFileHandler` (5 MB × 5 backups), DEBUG+.
- **In-app queue handler**: pushes formatted records onto a `queue.Queue`; `LogViewer` widget polls every 200 ms and appends to a virtualized listbox (max 5 000 lines).
- Format: `%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)-30s — %(message)s`.
- One `logging.getLogger(__name__)` per module. **No `print()` in src/.**
- Every job logs: input path (relative), recipe name, params, duration ms, input bytes → output bytes, ratio %, result status.
- Crash hook: uncaught exceptions go to `logs/crash-{ts}.log` with full traceback + system info; user sees a friendly modal with a "Copy crash report" button.
- Never log full file contents, EXIF GPS, or anything resembling PII.

---

## 9. Quality Gates (Non-Negotiable)

- [ ] `ruff check src tests` clean.
- [ ] `black --check src tests` clean.
- [ ] `mypy --strict src` clean.
- [ ] `pytest --cov=src/pixelforge/core --cov-fail-under=85` green.
- [ ] App launches with **zero warnings** on Python 3.11 and 3.12.
- [ ] No bare `except:`. No `print()` in `src/`. No hardcoded paths.
- [ ] All UI updates marshal to main thread via `widget.after()`.
- [ ] All long ops cancellable; `Esc` cancels the active batch within 200 ms.
- [ ] Graceful shutdown: cancel workers, flush logs, persist queue + settings.
- [ ] HighDPI verified on a 4K display.
- [ ] Conventional commits enforced via commit-msg hook.

---

## 10. README Requirements

The repo README must include, in this order:

1. Centered **logo** + tagline + 4 badges (Python, License, CI, Release).
2. **Hero GIF** showing drag-drop → batch compress → result.
3. **Why PixelForge** — 4 bullet pitch.
4. **Features** — checklist grouped by Convert / Resize / Compress / Batch / Power.
5. **Screenshots** — 3 to 5, dark mode, high quality.
6. **Install**:
   - Windows: download `.exe` from Releases.
   - From source: `git clone … && pip install -e .`
7. **Quick start** — 3 numbered steps with screenshots.
8. **CLI** — `pixelforge --help` snippet.
9. **Recipes** — what they are, how to make one, share one.
10. **Architecture** — mermaid `flowchart` of UI → Worker → Pipeline → Core.
11. **Roadmap**, **Contributing**, **Acknowledgements** (Lucide, Inter, Pillow, CustomTkinter), **License**.

---

## 11. GitHub Repository Setup

- **Name**: `pixelforge-studio` (suggest a different name only if taken).
- **Default branch**: `main`. Protect: require CI green + 1 approval (when collaborators exist).
- **Topics**: `python`, `image-processing`, `image-converter`, `image-resizer`, `image-compressor`, `desktop-app`, `customtkinter`, `pillow`, `gui`, `windows`.
- **About**: tagline + link to releases.
- **Releases**: tag `v1.0.0` triggers CI to build and attach `PixelForgeStudio-Setup-1.0.0.exe` and `PixelForgeStudio-1.0.0-portable.zip`.
- **Issue templates**: bug, feature, question.
- **Discussions**: enabled.
- **Sponsor**: optional `.github/FUNDING.yml`.

---

## 12. Definition of Done (v1.0.0)

- [ ] Repo scaffold matches Section 6 exactly.
- [ ] Logo set rendered (SVG + PNG + ICO) and used in title bar / About / installer.
- [ ] App launches via `python -m pixelforge` and via the built `.exe`.
- [ ] Drop a 5 MB photo → output ≤ 200 KB JPG in `output/`, visually intact.
- [ ] Batch of 30 mixed-format images processes without UI freeze, with live progress + logs + ETA.
- [ ] Codec battle mode shows MozJPEG vs WebP previews with size/quality.
- [ ] At least 3 shipped recipes work end-to-end.
- [ ] All quality gates (Section 9) pass in CI on Windows + Ubuntu, Python 3.11 + 3.12.
- [ ] PyInstaller produces a working signed-ready `PixelForgeStudio.exe` with the `.ico` embedded.
- [ ] README has hero GIF + 5 screenshots + working install path.
- [ ] Tagged `v1.0.0` release published with downloadable artifacts.

---

## 13. Build Order (recommended sprint plan)

**Sprint 1 — Foundation**
1. Repo scaffold, pyproject, ruff/black/mypy/pytest, pre-commit, CI green.
2. Logo design + asset generation script.
3. `core/compressor.py` + full test suite (the hardest part — get it right first).

**Sprint 2 — Core engine**
4. `core/converter.py`, `core/resizer.py`, `core/effects.py`.
5. `core/pipeline.py` + recipe model.
6. `logger.py`, `config.py`, `utils/`.

**Sprint 3 — UI shell**
7. `ui/theme.py`, `ui/icons.py`, custom titlebar, sidebar, status bar.
8. Drop zone, file queue with thumbnails, inspector panel.
9. Progress bar, log viewer, toasts.

**Sprint 4 — Workflows**
10. `workers/` — threaded batch executor, cancel/pause/resume.
11. Pages: Convert, Resize, Compress, Recipes, Stats, Logs, Settings.
12. Codec battle mode, side-by-side preview, histogram.

**Sprint 5 — Polish & ship**
13. i18n (en/tr/az), keyboard shortcuts, accessibility pass.
14. Crash handler, auto-update check, watch-folder mode.
15. PyInstaller spec, GitHub Release workflow, Inno Setup installer.
16. README, screenshots, demo GIF, v1.0.0 tag.

---

## 14. Engineering Principles

- **Boring is beautiful.** Prefer proven patterns over clever abstractions.
- **Easy to test, easy to delete.** When torn between two designs, choose the one that scores higher on both.
- **Source files are sacred.** Never overwrite an input unless the user explicitly opts in.
- **Fail loud, recover gracefully.** Log everything; show users a calm, actionable message.
- **Threads are dangerous.** Every cross-thread call goes through `widget.after()` or a `queue.Queue`. Never touch tk widgets from a worker thread.
- **No half-finished features.** Ship a smaller v1.0 with everything polished rather than a sprawling v0.7 that "almost works."
- **Conventional commits.** `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `perf:`, `style:`, `build:`, `ci:`. PR titles follow the same.

---

<div align="center">

**Begin with Sprint 1, Step 1: scaffold the repo and get CI green.**
**Then build the logo, then the compressor with its test suite.**
**Show your work step by step. Commit often. Ship a v1.0 you'd put on your resume.**

</div>
