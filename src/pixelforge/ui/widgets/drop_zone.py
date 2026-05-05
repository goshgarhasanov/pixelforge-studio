"""Şəkilləri sürükləyib buraxmaq üçün vidcet.

`tkinterdnd2` mövcuddursa, OS-səviyyəli sürükləməyə də cavab verir;
əks halda, yalnız klikləməklə fayl seçimi mümkündür.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from pixelforge.i18n import t
from pixelforge.ui import theme
from pixelforge.utils.formats import is_supported_input

# tkinterdnd2 isteğe bağlıdır.
try:  # pragma: no cover
    from tkinterdnd2 import DND_FILES  # type: ignore[import-not-found]

    HAS_DND = True
except Exception:  # pragma: no cover
    DND_FILES = None
    HAS_DND = False


class DropZone(ctk.CTkFrame):
    """Sürüklə-burax və klik ilə fayl seçimi üçün böyük zona."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_files_selected: Callable[[list[Path]], None],
    ) -> None:
        super().__init__(
            master,
            corner_radius=theme.RADIUS_LG,
            fg_color=theme.DARK_BG_ELEVATED,
            border_width=2,
            border_color=theme.DARK_BORDER,
        )
        self._callback = on_files_selected

        # İçindəki vidcetlər mərkəzdə yığılır.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=0)

        self._title = ctk.CTkLabel(
            inner,
            text=t("drop.title"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_DISPLAY, "bold"),
            text_color=theme.DARK_TEXT_PRIMARY,
        )
        self._title.pack(pady=(theme.SPACE_LG, theme.SPACE_XS))

        self._subtitle = ctk.CTkLabel(
            inner,
            text=t("drop.subtitle"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_BODY),
            text_color=theme.DARK_TEXT_SECONDARY,
        )
        self._subtitle.pack(pady=(0, theme.SPACE_LG))

        self._formats = ctk.CTkLabel(
            inner,
            text=t("drop.formats"),
            font=ctk.CTkFont(theme.FONT_MONO, theme.FS_SMALL),
            text_color=theme.DARK_TEXT_MUTED,
        )
        self._formats.pack(pady=(0, theme.SPACE_LG))

        # Klik hadisəsini bütün uşaq vidcetlərə bağlayırıq.
        for w in (self, inner, self._title, self._subtitle, self._formats):
            w.bind("<Button-1>", lambda _e: self._open_dialog())
            w.configure(cursor="hand2")

        # Sürüklə-burax dəstəyi.
        if HAS_DND:
            try:
                self.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
                self.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore[attr-defined]
                self.dnd_bind("<<DropEnter>>", self._on_drop_enter)  # type: ignore[attr-defined]
                self.dnd_bind("<<DropLeave>>", self._on_drop_leave)  # type: ignore[attr-defined]
            except Exception:
                pass

    def _on_drop_enter(self, _event: object) -> None:
        """Fayl üzərində dayandıqda sərhəddi işıqlandırır."""
        self.configure(border_color=theme.GRADIENT_FUCHSIA)

    def _on_drop_leave(self, _event: object) -> None:
        """Sərhədi normal vəziyyətə qaytarır."""
        self.configure(border_color=theme.DARK_BORDER)

    def _on_drop(self, event: object) -> None:
        """OS-dən gələn fayl yollarını ayırır və callback-i çağırır."""
        self._on_drop_leave(event)
        raw = getattr(event, "data", "") or ""
        # Windows-da yollar `{...}` ilə əhatə olunur, boşluqla ayrılır.
        paths: list[Path] = []
        token = ""
        in_brace = False
        for ch in raw:
            if ch == "{":
                in_brace = True
                continue
            if ch == "}":
                in_brace = False
                if token:
                    paths.append(Path(token))
                    token = ""
                continue
            if ch == " " and not in_brace:
                if token:
                    paths.append(Path(token))
                    token = ""
                continue
            token += ch
        if token:
            paths.append(Path(token))
        self._dispatch(paths)

    def _open_dialog(self) -> None:
        """Klikdə standart fayl seçimi dialoqunu açır."""
        filenames = filedialog.askopenfilenames(
            title=t("btn.add_files"),
            filetypes=[
                ("Şəkillər", "*.jpg *.jpeg *.png *.webp *.gif *.bmp *.tiff *.tif *.heic *.heif"),
                ("Bütün fayllar", "*.*"),
            ],
        )
        if not filenames:
            return
        self._dispatch([Path(f) for f in filenames])

    def _dispatch(self, paths: list[Path]) -> None:
        """Verilən yollardan dəstəklənən şəkilləri ayırır və qaytarır."""
        files: list[Path] = []
        for p in paths:
            if p.is_dir():
                files.extend(child for child in p.rglob("*") if is_supported_input(child))
            elif is_supported_input(p):
                files.append(p)
        if files:
            self._callback(files)
