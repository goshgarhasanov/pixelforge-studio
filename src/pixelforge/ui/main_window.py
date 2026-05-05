"""PixelForge Studio-nun əsas pəncərəsi.

Tam responsive düzüm:
  • Yuxarıda hero zolağı (uyğunlaşan).
  • PanedWindow ilə üfüqi və şaquli bölmələr — istifadəçi panel ölçülərini sürüşdürə bilər.
  • Aşağıda status bar.
  • Pəncərə minimum ölçüsünə çatdıqda da bütün vidcetlər görünməyə davam edir.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from pixelforge import __app_name__, __version__
from pixelforge.core.models import Job, JobStatus
from pixelforge.i18n import t
from pixelforge.ui import theme
from pixelforge.ui.widgets.drop_zone import HAS_DND, DropZone
from pixelforge.ui.widgets.error_dialog import show_error
from pixelforge.ui.widgets.file_queue import FileQueue
from pixelforge.ui.widgets.log_viewer import LogViewer
from pixelforge.ui.widgets.settings_panel import SettingsPanel
from pixelforge.ui.widgets.status_bar import StatusBar
from pixelforge.utils.paths import assets_dir
from pixelforge.workers.batch_worker import BatchWorker, WorkerEvent

logger = logging.getLogger(__name__)

WINDOW_TITLE = f"{__app_name__}  ·  v{__version__}"
WINDOW_MIN_SIZE = (840, 560)
WINDOW_INITIAL_SIZE = "1320x840"


class MainWindow(ctk.CTk):
    """Tətbiqin kök pəncərəsi və düzümü."""

    def __init__(self) -> None:
        # tkinterdnd2 mövcuddursa, sürüklə-burax üçün TkinterDnD ilə birgə işə salırıq.
        if HAS_DND:
            try:
                from tkinterdnd2 import TkinterDnD  # type: ignore[import-not-found]

                self.TkdndVersion = TkinterDnD._require(self)  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                pass
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_INITIAL_SIZE)
        self.minsize(*WINDOW_MIN_SIZE)
        self.configure(fg_color=theme.DARK_BG_BASE)

        # Pəncərə ikonu (Windows).
        try:
            ico_path = assets_dir() / "logo" / "icon.ico"
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
        except Exception:  # pragma: no cover
            pass

        self._worker = BatchWorker(max_workers=2)
        self._total_saved_bytes = 0
        self._jobs_done = 0
        self._jobs_failed = 0

        self._build_layout()
        self._poll_worker_events()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Klaviatura qısayolları.
        self.bind_all("<Control-o>", lambda _e: self._open_file_dialog())
        self.bind_all("<Control-Return>", lambda _e: self._start_batch())
        self.bind_all("<Escape>", lambda _e: self._cancel_batch())

    # ------------------------------------------------------------------
    # Düzüm qurulması
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Vidcetləri üçölçülü responsiv düzümdə yerləşdirir."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---- Hero (sabit hündürlük) ----
        hero = self._build_hero()
        hero.grid(row=0, column=0, sticky="we", padx=theme.SPACE_MD, pady=(theme.SPACE_MD, theme.SPACE_SM))

        # ---- Şaquli paned: yuxarıda iş sahəsi, aşağıda loglar ----
        v_paned = tk.PanedWindow(
            self,
            orient="vertical",
            sashrelief="flat",
            sashwidth=6,
            bg=theme.DARK_BG_BASE,
            bd=0,
        )
        v_paned.grid(row=1, column=0, sticky="nsew", padx=theme.SPACE_MD, pady=theme.SPACE_SM)

        # Üfüqi paned: solda drop+queue, sağda settings.
        h_paned = tk.PanedWindow(
            v_paned,
            orient="horizontal",
            sashrelief="flat",
            sashwidth=6,
            bg=theme.DARK_BG_BASE,
            bd=0,
        )

        left = ctk.CTkFrame(h_paned, fg_color="transparent")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=2, minsize=160)
        left.grid_rowconfigure(1, weight=3, minsize=160)

        self._drop_zone = DropZone(left, on_files_selected=self._add_files)
        self._drop_zone.grid(row=0, column=0, sticky="nsew", pady=(0, theme.SPACE_SM))

        self._file_queue = FileQueue(left, on_show_error=self._show_job_error)
        self._file_queue.grid(row=1, column=0, sticky="nsew", pady=(theme.SPACE_SM, 0))

        self._settings = SettingsPanel(h_paned, on_start=self._start_batch)

        h_paned.add(left, minsize=320, stretch="always")
        h_paned.add(self._settings, minsize=280, stretch="never", width=380)

        self._log_viewer = LogViewer(v_paned)

        v_paned.add(h_paned, minsize=280, stretch="always")
        v_paned.add(self._log_viewer, minsize=140, height=240, stretch="never")

        # ---- Status bar ----
        self._status_bar = StatusBar(self)
        self._status_bar.grid(row=2, column=0, sticky="we")

    def _build_hero(self) -> ctk.CTkFrame:
        """Yuxarıdakı brend zolağı + sürətli alət düymələri."""
        hero = ctk.CTkFrame(
            self,
            fg_color=theme.DARK_BG_ELEVATED,
            corner_radius=theme.RADIUS_LG,
            height=78,
        )
        hero.grid_columnconfigure(2, weight=1)
        hero.grid_propagate(False)

        # Loqo şəkli.
        try:
            logo_path = assets_dir() / "logo" / "logo-mark.png"
            if logo_path.exists():
                img = Image.open(logo_path).resize((48, 48), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(48, 48))
                ctk.CTkLabel(hero, image=ctk_img, text="").grid(
                    row=0, column=0, rowspan=2, padx=(theme.SPACE_LG, theme.SPACE_SM), pady=theme.SPACE_SM
                )
        except Exception:  # pragma: no cover
            pass

        ctk.CTkLabel(
            hero,
            text=__app_name__,
            font=ctk.CTkFont(theme.FONT_FAMILY, 20, "bold"),
            text_color=theme.DARK_TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=1, sticky="sw", pady=(theme.SPACE_SM, 0))

        ctk.CTkLabel(
            hero,
            text=t("app.tagline"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            text_color=theme.GRADIENT_FUCHSIA,
            anchor="w",
        ).grid(row=1, column=1, sticky="nw", pady=(0, theme.SPACE_SM))

        # Sağ tərəfdə düymələr.
        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.grid(row=0, column=3, rowspan=2, sticky="e", padx=theme.SPACE_LG)

        ctk.CTkButton(
            actions,
            text="📁  " + t("btn.add_files"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL, "bold"),
            height=34,
            corner_radius=theme.RADIUS_MD,
            fg_color=theme.GRADIENT_INDIGO,
            hover_color=theme.GRADIENT_FUCHSIA,
            command=self._open_file_dialog,
        ).grid(row=0, column=0, padx=4)

        ctk.CTkButton(
            actions,
            text="🗑  " + t("btn.clear"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            height=34,
            corner_radius=theme.RADIUS_MD,
            fg_color=theme.DARK_BG_BASE,
            hover_color=theme.DARK_BG_OVERLAY,
            text_color=theme.DARK_TEXT_SECONDARY,
            command=self._clear_queue,
        ).grid(row=0, column=1, padx=4)

        ctk.CTkButton(
            actions,
            text="📂  " + t("btn.open_output"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            height=34,
            corner_radius=theme.RADIUS_MD,
            fg_color=theme.ACCENT_VIOLET,
            hover_color=theme.GRADIENT_FUCHSIA,
            command=self._open_output_dir,
        ).grid(row=0, column=2, padx=4)

        return hero

    # ------------------------------------------------------------------
    # Hadisə işləyiciləri
    # ------------------------------------------------------------------
    def _open_file_dialog(self) -> None:
        """Hero düyməsindən fayl seçimini başladır."""
        self._drop_zone._open_dialog()  # noqa: SLF001

    def _add_files(self, files: list[Path]) -> None:
        """Verilmiş fayllardan iş yaradıb növbəyə qoyur."""
        opts = self._settings.build_options()
        new_jobs: list[Job] = []
        invalid: list[str] = []
        for p in files:
            try:
                size = p.stat().st_size
            except OSError as exc:
                invalid.append(f"{p.name}: {exc}")
                continue
            j = Job(source=p, options=opts)
            j.original_size = size
            new_jobs.append(j)

        if invalid:
            show_error(
                self,
                title="Bəzi fayllar əlavə edilə bilmədi",
                message="Aşağıdakı fayllara giriş mümkün olmadı.",
                suggestion="Faylların mövcudluğunu və icazələri yoxlayın.",
                affected_files=invalid,
            )

        if new_jobs:
            self._file_queue.add_jobs(new_jobs)
            self._status_bar.set_files(len(self._file_queue.jobs()))
            logger.info("Növbəyə %d fayl əlavə edildi", len(new_jobs))

    def _clear_queue(self) -> None:
        """Növbəni tamamilə təmizləyir."""
        if self._worker.is_running:
            logger.warning("Toplu emal davam edir — təmizləmə icazəli deyil")
            show_error(
                self,
                title="Növbəni təmizləmək olmaz",
                message="Toplu emal hazırda davam edir.",
                suggestion="Əvvəlcə Esc düyməsi ilə emalı dayandırın.",
            )
            return
        self._file_queue.clear()
        self._status_bar.set_files(0)
        self._status_bar.set_saved(0)
        self._total_saved_bytes = 0
        self._jobs_done = 0
        self._jobs_failed = 0

    def _open_output_dir(self) -> None:
        """Çıxış qovluğunu sistemin fayl meneceri ilə açır."""
        from pixelforge.utils.paths import output_dir

        target = output_dir()
        try:
            import os
            import sys

            if sys.platform.startswith("win"):
                os.startfile(str(target))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                import subprocess

                subprocess.Popen(["open", str(target)])
            else:
                import subprocess

                subprocess.Popen(["xdg-open", str(target)])
        except Exception as exc:  # noqa: BLE001
            logger.error("Qovluq açıla bilmədi: %s", exc)
            show_error(
                self,
                title="Qovluq açıla bilmədi",
                message=f"Çıxış qovluğunu açmaq mümkün olmadı: {exc}",
                suggestion="Qovluğun mövcudluğunu yoxlayın.",
            )

    def _start_batch(self) -> None:
        """Növbədəki bütün işləri emal etməyə başlayır."""
        jobs = self._file_queue.jobs()
        if not jobs:
            logger.warning(t("toast.no_files"))
            self._status_bar.set_status("status.failed", color=theme.STATUS_FAILED)
            show_error(
                self,
                title="Heç bir fayl yoxdur",
                message="Növbədə emal ediləcək heç bir şəkil yoxdur.",
                suggestion="Əvvəlcə şəkilləri sürükləyib bura buraxın və ya Fayl əlavə et düyməsinə klikləyin.",
            )
            return
        if self._worker.is_running:
            logger.info("Toplu emal artıq icra olunur")
            return

        # Yeni parametrlərlə bütün işləri yeniləyirik.
        try:
            opts = self._settings.build_options()
        except Exception as exc:  # noqa: BLE001
            import traceback as _tb

            show_error(
                self,
                title="Tənzimləmələrdə xəta",
                message=str(exc),
                suggestion="En, hündürlük və hədəf KB sahələrində ədəd olduğunu yoxlayın.",
                traceback_text=_tb.format_exc(),
            )
            return

        for j in jobs:
            j.options = opts
            j.status = JobStatus.QUEUED
            j.error = None
            j.error_suggestion = None
            j.error_traceback = None
        self._jobs_done = 0
        self._jobs_failed = 0
        self._total_saved_bytes = 0
        self._status_bar.set_saved(0)

        self._status_bar.set_status("status.running", color=theme.STATUS_RUNNING)
        logger.info(t("toast.batch_started"))
        self._worker.start(jobs)

    def _cancel_batch(self) -> None:
        """Cari emal əməliyyatını dayandırır."""
        if self._worker.is_running:
            logger.info("İstifadəçi tərəfindən ləğv edildi")
            self._worker.cancel()

    def _show_job_error(self, job: Job) -> None:
        """Verilmiş iş üçün geniş xəta dialoqunu göstərir."""
        if job.status != JobStatus.FAILED:
            return
        show_error(
            self,
            title="Şəkil emal edilə bilmədi",
            message=job.error or "Naməlum xəta.",
            suggestion=job.error_suggestion or "",
            traceback_text=job.error_traceback or "",
            affected_files=[str(job.source)],
        )

    # ------------------------------------------------------------------
    # İşçi hadisələrinin oxunması
    # ------------------------------------------------------------------
    def _poll_worker_events(self) -> None:
        """İşçi növbəsindən hadisələri çəkib UI-ni yeniləyir."""
        try:
            while True:
                event: WorkerEvent = self._worker.events.get_nowait()
                self._handle_event(event)
        except Exception:
            pass
        self.after(150, self._poll_worker_events)

    def _handle_event(self, event: WorkerEvent) -> None:
        """Bir işçi hadisəsini emal edir və UI-ni yeniləyir."""
        if event.kind in ("job_started", "job_done", "job_failed"):
            if event.job_index >= 0:
                self._file_queue.refresh_job(event.job_index)
            if event.kind == "job_done" and event.job is not None:
                self._jobs_done += 1
                self._total_saved_bytes += event.job.saved_bytes
                self._status_bar.set_saved(self._total_saved_bytes)
            elif event.kind == "job_failed":
                self._jobs_failed += 1
        elif event.kind == "batch_done":
            if self._jobs_failed:
                self._status_bar.set_status("status.failed", color=theme.STATUS_FAILED)
            else:
                self._status_bar.set_status("status.done", color=theme.STATUS_DONE)
            logger.info(
                "%s — %d uğurlu, %d xətalı",
                t("toast.batch_done"),
                self._jobs_done,
                self._jobs_failed,
            )

    def _on_close(self) -> None:
        """Pəncərə bağlananda işçini dayandırır və çıxır."""
        try:
            if self._worker.is_running:
                self._worker.cancel()
                self._worker.join(timeout=2.0)
        except Exception:  # pragma: no cover
            pass
        try:
            self.destroy()
        finally:
            for thr in threading.enumerate():
                if thr is threading.main_thread():
                    continue
                # daemon thread-lər proses bitincə öləcək
