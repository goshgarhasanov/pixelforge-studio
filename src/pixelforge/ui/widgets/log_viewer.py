"""Tətbiq daxilində canlı log axınını göstərən vidcet."""

from __future__ import annotations

import queue

import customtkinter as ctk

from pixelforge.i18n import t
from pixelforge.logger import get_ui_log_queue
from pixelforge.ui import theme

# UI yeniləmə intervalı (millisaniyə).
POLL_INTERVAL_MS = 250
MAX_LINES = 1000


class LogViewer(ctk.CTkFrame):
    """Loglama növbəsindən gələn mesajları göstərən sürüşkən mətn qutusu."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.DARK_BG_ELEVATED, corner_radius=theme.RADIUS_LG)
        self._queue: queue.Queue[str] = get_ui_log_queue()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Başlıq + təmizlə düyməsi.
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_MD, 0))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            head,
            text=t("logs.title"),
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_TITLE, "bold"),
            text_color=theme.DARK_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="we")
        ctk.CTkButton(
            head,
            text=t("logs.clear"),
            width=110,
            height=28,
            fg_color=theme.DARK_BG_BASE,
            hover_color=theme.DARK_BG_OVERLAY,
            text_color=theme.DARK_TEXT_SECONDARY,
            command=self.clear,
        ).grid(row=0, column=1)

        # Mətn qutusu.
        self._textbox = ctk.CTkTextbox(
            self,
            fg_color=theme.DARK_BG_DEEPEST,
            text_color=theme.DARK_TEXT_PRIMARY,
            font=ctk.CTkFont(theme.FONT_MONO, theme.FS_SMALL),
            wrap="none",
            corner_radius=theme.RADIUS_MD,
            border_width=0,
        )
        self._textbox.grid(row=1, column=0, sticky="nsew", padx=theme.SPACE_SM, pady=theme.SPACE_SM)
        self._textbox.configure(state="disabled")

        self._line_count = 0
        self.after(POLL_INTERVAL_MS, self._poll)

    def _poll(self) -> None:
        """Növbədən gələn mesajları oxuyur və mətn qutusuna əlavə edir."""
        drained = 0
        try:
            while drained < 50:  # bir dövrdə həddən çox iş görməyək
                line = self._queue.get_nowait()
                self._append(line)
                drained += 1
        except queue.Empty:
            pass
        self.after(POLL_INTERVAL_MS, self._poll)

    def _append(self, text: str) -> None:
        """Mətn qutusunun sonuna sətir əlavə edir, lazımdırsa köhnələri silir."""
        self._textbox.configure(state="normal")
        self._textbox.insert("end", text + "\n")
        self._line_count += 1
        if self._line_count > MAX_LINES:
            # Yaddaş qənaətinə görə yuxarıdan sətirlər silinir.
            self._textbox.delete("1.0", "100.0")
            self._line_count -= 100
        self._textbox.see("end")
        self._textbox.configure(state="disabled")

    def clear(self) -> None:
        """Bütün logları təmizləyir."""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")
        self._line_count = 0
