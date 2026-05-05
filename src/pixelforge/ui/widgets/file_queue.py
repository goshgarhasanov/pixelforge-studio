"""Şəkillərin emal növbəsini göstərən vidcet."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from pixelforge.core.models import Job, JobStatus
from pixelforge.i18n import t
from pixelforge.ui import theme
from pixelforge.utils.humanize import human_bytes


_STATUS_COLORS = {
    JobStatus.QUEUED: theme.STATUS_QUEUED,
    JobStatus.RUNNING: theme.STATUS_RUNNING,
    JobStatus.DONE: theme.STATUS_DONE,
    JobStatus.FAILED: theme.STATUS_FAILED,
    JobStatus.CANCELLED: theme.STATUS_CANCELLED,
}

_STATUS_LABELS = {
    JobStatus.QUEUED: "queued",
    JobStatus.RUNNING: "running",
    JobStatus.DONE: "done",
    JobStatus.FAILED: "failed",
    JobStatus.CANCELLED: "cancelled",
}


class _JobRow(ctk.CTkFrame):
    """Növbədə bir işin (bir şəklin) göstərildiyi sıra."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        job: Job,
        on_remove: Callable[[Job], None],
    ) -> None:
        super().__init__(
            master,
            fg_color=theme.DARK_BG_BASE,
            corner_radius=theme.RADIUS_MD,
            height=44,
        )
        self.job = job
        self._on_remove = on_remove

        self.grid_columnconfigure(0, weight=1)

        self._name = ctk.CTkLabel(
            self,
            text=job.source.name,
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_BODY),
            text_color=theme.DARK_TEXT_PRIMARY,
        )
        self._name.grid(row=0, column=0, sticky="we", padx=(theme.SPACE_MD, theme.SPACE_SM), pady=8)

        self._size = ctk.CTkLabel(
            self,
            text=human_bytes(job.original_size or job.source.stat().st_size),
            font=ctk.CTkFont(theme.FONT_MONO, theme.FS_SMALL),
            text_color=theme.DARK_TEXT_SECONDARY,
            width=80,
        )
        self._size.grid(row=0, column=1, padx=theme.SPACE_SM)

        self._arrow = ctk.CTkLabel(self, text="→", text_color=theme.DARK_TEXT_MUTED, width=20)
        self._arrow.grid(row=0, column=2)

        self._target = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(theme.FONT_MONO, theme.FS_SMALL),
            text_color=theme.DARK_TEXT_SECONDARY,
            width=80,
        )
        self._target.grid(row=0, column=3, padx=theme.SPACE_SM)

        self._status = ctk.CTkLabel(
            self,
            text=t(f"status.{_STATUS_LABELS[job.status]}"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL, "bold"),
            text_color=_STATUS_COLORS[job.status],
            width=100,
        )
        self._status.grid(row=0, column=4, padx=theme.SPACE_SM)

        self._remove_btn = ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            corner_radius=theme.RADIUS_SM,
            fg_color="transparent",
            hover_color=theme.DARK_BG_OVERLAY,
            text_color=theme.DARK_TEXT_MUTED,
            command=lambda: self._on_remove(self.job),
        )
        self._remove_btn.grid(row=0, column=5, padx=(theme.SPACE_SM, theme.SPACE_MD))

    def refresh(self) -> None:
        """Status və hədəf ölçü etiketlərini cari vəziyyətə uyğunlaşdırır."""
        self._status.configure(
            text=t(f"status.{_STATUS_LABELS[self.job.status]}"),
            text_color=_STATUS_COLORS[self.job.status],
        )
        if self.job.final_size:
            self._target.configure(
                text=human_bytes(self.job.final_size),
                text_color=theme.STATUS_DONE,
            )
        elif self.job.status == JobStatus.FAILED:
            self._target.configure(text="—", text_color=theme.STATUS_FAILED)


class FileQueue(ctk.CTkFrame):
    """İşlərin sıralandığı sürüşkən növbə paneli."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.DARK_BG_ELEVATED, corner_radius=theme.RADIUS_LG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Başlıq.
        self._header = ctk.CTkLabel(
            self,
            text=t("queue.title") + "  (0)",
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_TITLE, "bold"),
            text_color=theme.DARK_TEXT_PRIMARY,
        )
        self._header.grid(row=0, column=0, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_MD, 0))

        # Sürüşkən sahə.
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=theme.SPACE_SM, pady=theme.SPACE_SM)
        self._scroll.grid_columnconfigure(0, weight=1)

        # Boş vəziyyət etiketi.
        self._empty = ctk.CTkLabel(
            self._scroll,
            text=t("queue.empty"),
            text_color=theme.DARK_TEXT_MUTED,
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_BODY),
        )
        self._empty.grid(row=0, column=0, pady=theme.SPACE_2XL)

        self._rows: list[_JobRow] = []
        self._jobs: list[Job] = []

    def jobs(self) -> list[Job]:
        """Cari növbədəki bütün işləri qaytarır."""
        return list(self._jobs)

    def add_jobs(self, jobs: list[Job]) -> None:
        """Növbəyə yeni işlər əlavə edir."""
        if jobs and self._empty.winfo_ismapped():
            self._empty.grid_forget()
        for job in jobs:
            row = _JobRow(self._scroll, job, on_remove=self._remove_job)
            row.grid(
                row=len(self._rows),
                column=0,
                sticky="we",
                padx=theme.SPACE_SM,
                pady=4,
            )
            self._rows.append(row)
            self._jobs.append(job)
        self._update_header()

    def _remove_job(self, job: Job) -> None:
        """Növbədən bir işi silir."""
        for i, row in enumerate(self._rows):
            if row.job is job:
                row.destroy()
                del self._rows[i]
                self._jobs.remove(job)
                break
        if not self._rows:
            self._empty.grid(row=0, column=0, pady=theme.SPACE_2XL)
        self._update_header()

    def clear(self) -> None:
        """Bütün işləri silir."""
        for row in self._rows:
            row.destroy()
        self._rows.clear()
        self._jobs.clear()
        self._empty.grid(row=0, column=0, pady=theme.SPACE_2XL)
        self._update_header()

    def refresh_job(self, index: int) -> None:
        """Verilmiş indeksdə olan işin sırasını yeniləyir."""
        if 0 <= index < len(self._rows):
            self._rows[index].refresh()

    def _update_header(self) -> None:
        """Başlıqdakı sayğacı yeniləyir."""
        self._header.configure(text=f"{t('queue.title')}  ({len(self._rows)})")
