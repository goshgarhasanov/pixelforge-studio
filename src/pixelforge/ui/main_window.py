"""PixelForge Studio-nun əsas pəncərəsi."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from pixelforge import __app_name__, __version__
from pixelforge.core.models import Job, JobStatus
from pixelforge.i18n import t
from pixelforge.ui import theme
from pixelforge.ui.widgets.drop_zone import HAS_DND, DropZone
from pixelforge.ui.widgets.file_queue import FileQueue
from pixelforge.ui.widgets.log_viewer import LogViewer
from pixelforge.ui.widgets.settings_panel import SettingsPanel
from pixelforge.ui.widgets.status_bar import StatusBar
from pixelforge.utils.paths import assets_dir
from pixelforge.workers.batch_worker import BatchWorker, WorkerEvent

logger = logging.getLogger(__name__)

# Pəncərə üçün standart başlıq.
WINDOW_TITLE = f"{__app_name__}  ·  v{__version__}"
WINDOW_MIN_SIZE = (1100, 700)
WINDOW_INITIAL_SIZE = "1280x800"


class MainWindow(ctk.CTk):
    """Tətbiqin kök pəncərəsi və düzümü."""

    def __init__(self) -> None:
        # tkinterdnd2 mövcuddursa, sürüklə-burax üçün TkinterDnD.Tk istifadə olunur.
        if HAS_DND:
            try:
                from tkinterdnd2 import TkinterDnD  # type: ignore[import-not-found]

                # CustomTkinter-i TkinterDnD ilə uyğunlaşdırırıq.
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

        # Pəncərə ikonu (yalnız Windows-da işləyir).
        try:
            ico_path = assets_dir() / "logo" / "icon.ico"
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
        except Exception:  # pragma: no cover
            pass

        self._worker = BatchWorker(max_workers=2)
        self._total_saved_bytes = 0

        self._build_layout()
        self._poll_worker_events()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Düzüm qurulması
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Bütün vidcetləri yerləşdirir."""
        # 0-cu sıra: hero (loqo + tagline).
        # 1-ci sıra: əsas məzmun (sol: drop+queue, sağ: settings, alt: log).
        # 2-ci sıra: status bar.
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=2)

        # ---- Hero ----
        hero = self._build_hero()
        hero.grid(row=0, column=0, columnspan=2, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_LG, theme.SPACE_SM))

        # ---- Sol sütun: drop zone + queue ----
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(theme.SPACE_LG, theme.SPACE_SM), pady=theme.SPACE_SM)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=2)

        self._drop_zone = DropZone(left, on_files_selected=self._add_files)
        self._drop_zone.grid(row=0, column=0, sticky="nsew", pady=(0, theme.SPACE_SM))

        self._file_queue = FileQueue(left)
        self._file_queue.grid(row=1, column=0, sticky="nsew", pady=(theme.SPACE_SM, 0))

        # ---- Sağ sütun: tənzimləmələr ----
        self._settings = SettingsPanel(self, on_start=self._start_batch)
        self._settings.grid(row=1, column=1, sticky="nsew", padx=(theme.SPACE_SM, theme.SPACE_LG), pady=theme.SPACE_SM)

        # ---- Alt: log viewer (iki sütunu da əhatə edir) ----
        self._log_viewer = LogViewer(self)
        self._log_viewer.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=theme.SPACE_LG, pady=theme.SPACE_SM)

        # ---- Status bar ----
        self._status_bar = StatusBar(self)
        self._status_bar.grid(row=3, column=0, columnspan=2, sticky="we")

    def _build_hero(self) -> ctk.CTkFrame:
        """Yuxarıdakı qradient hero zolağını qurur."""
        hero = ctk.CTkFrame(
            self,
            fg_color=theme.DARK_BG_ELEVATED,
            corner_radius=theme.RADIUS_LG,
            height=84,
        )
        hero.grid_columnconfigure(2, weight=1)

        # Loqo şəkli (assets-dən).
        try:
            logo_path = assets_dir() / "logo" / "logo-mark.png"
            if logo_path.exists():
                img = Image.open(logo_path).resize((52, 52), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(52, 52))
                ctk.CTkLabel(hero, image=ctk_img, text="").grid(
                    row=0, column=0, rowspan=2, padx=(theme.SPACE_LG, theme.SPACE_SM), pady=theme.SPACE_MD
                )
        except Exception:  # pragma: no cover
            pass

        ctk.CTkLabel(
            hero,
            text=__app_name__,
            font=ctk.CTkFont(theme.FONT_FAMILY, 22, "bold"),
            text_color=theme.DARK_TEXT_PRIMARY,
        ).grid(row=0, column=1, sticky="sw", pady=(theme.SPACE_MD, 0))

        ctk.CTkLabel(
            hero,
            text=t("app.tagline"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            text_color=theme.GRADIENT_FUCHSIA,
        ).grid(row=1, column=1, sticky="nw", pady=(0, theme.SPACE_MD))

        # Sağ tərəfdə alət düymələri.
        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.grid(row=0, column=3, rowspan=2, sticky="e", padx=theme.SPACE_LG)

        ctk.CTkButton(
            actions,
            text="📁  " + t("btn.add_files"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL, "bold"),
            height=36,
            corner_radius=theme.RADIUS_MD,
            fg_color=theme.GRADIENT_INDIGO,
            hover_color=theme.GRADIENT_FUCHSIA,
            command=self._open_file_dialog,
        ).grid(row=0, column=0, padx=4)

        ctk.CTkButton(
            actions,
            text="🗑  " + t("btn.clear"),
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            height=36,
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
            height=36,
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
        self._drop_zone._open_dialog()  # noqa: SLF001 — daxili istifadə

    def _add_files(self, files: list[Path]) -> None:
        """Verilmiş fayllardan iş yaradıb növbəyə qoyur."""
        opts = self._settings.build_options()
        new_jobs = [Job(source=p, options=opts) for p in files]
        for j in new_jobs:
            try:
                j.original_size = j.source.stat().st_size
            except OSError:
                pass
        self._file_queue.add_jobs(new_jobs)
        self._status_bar.set_files(len(self._file_queue.jobs()))
        logger.info("Növbəyə %d fayl əlavə edildi", len(new_jobs))

    def _clear_queue(self) -> None:
        """Növbəni tamamilə təmizləyir."""
        if self._worker.is_running:
            logger.warning("Toplu emal davam edir — təmizləmə icazəli deyil")
            return
        self._file_queue.clear()
        self._status_bar.set_files(0)
        self._status_bar.set_saved(0)
        self._total_saved_bytes = 0

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

    def _start_batch(self) -> None:
        """Növbədəki bütün işləri emal etməyə başlayır."""
        jobs = self._file_queue.jobs()
        if not jobs:
            logger.warning(t("toast.no_files"))
            self._status_bar.set_status("status.failed", color=theme.STATUS_FAILED)
            return
        if self._worker.is_running:
            logger.info("Toplu emal artıq icra olunur")
            return

        # Yeni parametrlər ilə bütün işləri yeniləyirik.
        opts = self._settings.build_options()
        for j in jobs:
            j.options = opts
            j.status = JobStatus.QUEUED
            j.error = None

        self._status_bar.set_status("status.running", color=theme.STATUS_RUNNING)
        logger.info(t("toast.batch_started"))
        self._worker.start(jobs)

    # ------------------------------------------------------------------
    # İşçi hadisələrinin oxunması (UI thread)
    # ------------------------------------------------------------------
    def _poll_worker_events(self) -> None:
        """İşçi növbəsindən hadisələri çəkib UI-ni yeniləyir."""
        try:
            while True:
                event: WorkerEvent = self._worker.events.get_nowait()
                self._handle_event(event)
        except Exception:
            # Növbə boşdur — sadəcə davam edirik.
            pass
        self.after(150, self._poll_worker_events)

    def _handle_event(self, event: WorkerEvent) -> None:
        """Bir işçi hadisəsini emal edir və müvafiq UI dəyişikliklərini tətbiq edir."""
        if event.kind in ("job_started", "job_done", "job_failed"):
            if event.job_index >= 0:
                self._file_queue.refresh_job(event.job_index)
            if event.kind == "job_done" and event.job is not None:
                self._total_saved_bytes += event.job.saved_bytes
                self._status_bar.set_saved(self._total_saved_bytes)
        elif event.kind == "batch_done":
            self._status_bar.set_status("status.done", color=theme.STATUS_DONE)
            logger.info(t("toast.batch_done"))

    def _on_close(self) -> None:
        """Pəncərə bağlananda işçini dayandırır və çıxır."""
        try:
            if self._worker.is_running:
                self._worker.cancel()
                self._worker.join(timeout=2.0)
        except Exception:  # pragma: no cover
            pass
        # Daemon thread-lər varsa, force exit.
        try:
            self.destroy()
        finally:
            for thr in threading.enumerate():
                if thr is threading.main_thread():
                    continue
                # daemon olduğundan proses bitincə öləcək
