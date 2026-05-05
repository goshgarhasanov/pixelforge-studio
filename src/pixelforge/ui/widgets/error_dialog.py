"""Geniş, müasir xəta dialoqu.

Xüsusiyyətlər:
  • İkon + qısa başlıq + uzun izahat.
  • Təklif sahəsi (xətanı necə həll etmək).
  • Genişləndirilə bilən "Texniki detallar" — tam traceback.
  • "Köçür" düyməsi — bütün xəta hesabatını sistemə köçürür.
  • "Bağla" düyməsi.
"""

from __future__ import annotations

import platform
import sys
from typing import Iterable

import customtkinter as ctk

from pixelforge import __version__
from pixelforge.ui import theme


class ErrorDialog(ctk.CTkToplevel):
    """Modal xəta dialoqu."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        title: str,
        message: str,
        suggestion: str = "",
        traceback_text: str = "",
        affected_files: Iterable[str] = (),
    ) -> None:
        super().__init__(master)
        self.title("Xəta — PixelForge Studio")
        self.geometry("640x520")
        self.minsize(520, 400)
        self.configure(fg_color=theme.DARK_BG_BASE)
        self.transient(master)  # type: ignore[arg-type]
        self.grab_set()

        self._title = title
        self._message = message
        self._suggestion = suggestion
        self._traceback = traceback_text
        self._affected = list(affected_files)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_message_area()
        self._build_details()
        self._build_buttons()

        # ESC ilə bağlamaq.
        self.bind("<Escape>", lambda _e: self.destroy())

        # Mərkəzə yerləşdir.
        self.update_idletasks()
        try:
            mx = master.winfo_rootx() + (master.winfo_width() // 2)  # type: ignore[union-attr]
            my = master.winfo_rooty() + (master.winfo_height() // 2)  # type: ignore[union-attr]
            w = self.winfo_width()
            h = self.winfo_height()
            self.geometry(f"+{mx - w // 2}+{my - h // 2}")
        except Exception:  # pragma: no cover
            pass

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        """Yuxarıda ikon + başlıq."""
        hdr = ctk.CTkFrame(self, fg_color=theme.STATUS_FAILED, corner_radius=0, height=72)
        hdr.grid(row=0, column=0, sticky="we")
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hdr,
            text="⚠",
            font=ctk.CTkFont(theme.FONT_FAMILY, 36, "bold"),
            text_color="#FFFFFF",
        ).grid(row=0, column=0, padx=(theme.SPACE_LG, theme.SPACE_MD), pady=theme.SPACE_MD)

        ctk.CTkLabel(
            hdr,
            text=self._title,
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_DISPLAY - 4, "bold"),
            text_color="#FFFFFF",
        ).grid(row=0, column=1, sticky="we", pady=theme.SPACE_MD)

    def _build_message_area(self) -> None:
        """Əsas mesaj + təklif."""
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_LG, 0))
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            body,
            text=self._message,
            anchor="w",
            justify="left",
            wraplength=580,
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_BODY),
            text_color=theme.DARK_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="we")

        if self._suggestion:
            ctk.CTkLabel(
                body,
                text="💡  " + self._suggestion,
                anchor="w",
                justify="left",
                wraplength=580,
                font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
                text_color=theme.ACCENT_SUNFLOWER,
            ).grid(row=1, column=0, sticky="we", pady=(theme.SPACE_MD, 0))

        if self._affected:
            files_text = "Təsirlənən fayl(lar):\n" + "\n".join(f"  • {n}" for n in self._affected[:8])
            if len(self._affected) > 8:
                files_text += f"\n  …və daha {len(self._affected) - 8} fayl"
            ctk.CTkLabel(
                body,
                text=files_text,
                anchor="w",
                justify="left",
                font=ctk.CTkFont(theme.FONT_MONO, theme.FS_SMALL),
                text_color=theme.DARK_TEXT_SECONDARY,
            ).grid(row=2, column=0, sticky="we", pady=(theme.SPACE_MD, 0))

    def _build_details(self) -> None:
        """Texniki traceback paneli (gizli, açıla bilər)."""
        wrap = ctk.CTkFrame(self, fg_color=theme.DARK_BG_ELEVATED, corner_radius=theme.RADIUS_MD)
        wrap.grid(row=2, column=0, sticky="nsew", padx=theme.SPACE_LG, pady=theme.SPACE_LG)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(wrap, fg_color="transparent")
        head.grid(row=0, column=0, sticky="we", padx=theme.SPACE_MD, pady=(theme.SPACE_SM, 0))
        head.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            head,
            text="🛠  Texniki detallar",
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL, "bold"),
            text_color=theme.DARK_TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w")

        textbox = ctk.CTkTextbox(
            wrap,
            font=ctk.CTkFont(theme.FONT_MONO, theme.FS_TINY),
            fg_color=theme.DARK_BG_DEEPEST,
            text_color=theme.DARK_TEXT_SECONDARY,
            corner_radius=theme.RADIUS_SM,
            border_width=0,
            wrap="none",
        )
        textbox.grid(row=1, column=0, sticky="nsew", padx=theme.SPACE_SM, pady=theme.SPACE_SM)
        textbox.insert("1.0", self._compose_report())
        textbox.configure(state="disabled")

    def _build_buttons(self) -> None:
        """Aşağıdakı düymələr."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="we", padx=theme.SPACE_LG, pady=(0, theme.SPACE_LG))
        bar.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            bar,
            text="⧉  Hesabatı köçür",
            width=160,
            height=36,
            fg_color=theme.ACCENT_VIOLET,
            hover_color=theme.GRADIENT_FUCHSIA,
            command=self._copy_report,
        ).grid(row=0, column=1, padx=(0, theme.SPACE_SM))

        ctk.CTkButton(
            bar,
            text="Bağla",
            width=100,
            height=36,
            fg_color=theme.DARK_BG_OVERLAY,
            hover_color=theme.STATUS_FAILED,
            command=self.destroy,
        ).grid(row=0, column=2)

    # ------------------------------------------------------------------
    def _compose_report(self) -> str:
        """Bütün detalları bir hesabat mətninə yığır."""
        lines: list[str] = []
        lines.append(f"PixelForge Studio v{__version__}")
        lines.append(f"Python {sys.version.split()[0]}  ·  {platform.platform()}")
        lines.append("")
        lines.append(f"Başlıq:    {self._title}")
        lines.append(f"Mesaj:     {self._message}")
        if self._suggestion:
            lines.append(f"Təklif:    {self._suggestion}")
        if self._affected:
            lines.append("")
            lines.append("Təsirlənən fayllar:")
            lines.extend(f"  - {n}" for n in self._affected)
        if self._traceback:
            lines.append("")
            lines.append("─" * 60)
            lines.append("Traceback:")
            lines.append(self._traceback)
        return "\n".join(lines)

    def _copy_report(self) -> None:
        """Hesabatı sistem buferinə qoyur."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self._compose_report())
        except Exception:  # pragma: no cover
            pass


def show_error(
    master: ctk.CTkBaseClass,
    *,
    title: str,
    message: str,
    suggestion: str = "",
    traceback_text: str = "",
    affected_files: Iterable[str] = (),
) -> None:
    """Asan istifadə üçün köməkçi funksiya."""
    ErrorDialog(
        master,
        title=title,
        message=message,
        suggestion=suggestion,
        traceback_text=traceback_text,
        affected_files=affected_files,
    )
