"""Tətbiqin alt status zolağı."""

from __future__ import annotations

import customtkinter as ctk

from pixelforge.i18n import t
from pixelforge.ui import theme
from pixelforge.utils.humanize import human_bytes


class StatusBar(ctk.CTkFrame):
    """Aşağıda dayanan status bar — fayl sayı, qənaət, vəziyyət göstərir."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.DARK_BG_DEEPEST, corner_radius=0, height=28)

        self.grid_columnconfigure(1, weight=1)

        self._status = ctk.CTkLabel(
            self,
            text="● " + t("status.ready"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            text_color=theme.STATUS_DONE,
            anchor="w",
        )
        self._status.grid(row=0, column=0, padx=theme.SPACE_LG, sticky="w")

        self._files = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            text_color=theme.DARK_TEXT_SECONDARY,
            anchor="center",
        )
        self._files.grid(row=0, column=1, sticky="we")

        self._saved = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            text_color=theme.STATUS_DONE,
            anchor="e",
        )
        self._saved.grid(row=0, column=2, padx=theme.SPACE_LG, sticky="e")

    def set_status(self, key: str, color: str | None = None) -> None:
        """Status mesajını dəyişir (məs. 'status.running')."""
        self._status.configure(text="● " + t(key))
        if color:
            self._status.configure(text_color=color)

    def set_files(self, count: int) -> None:
        """Növbədəki fayl sayını yeniləyir."""
        self._files.configure(text=t("statusbar.files", n=count) if count else "")

    def set_saved(self, total_bytes: int) -> None:
        """Ümumi qənaət edilmiş bayt miqdarını göstərir."""
        if total_bytes > 0:
            self._saved.configure(text=t("statusbar.saved", size=human_bytes(total_bytes)))
        else:
            self._saved.configure(text="")
