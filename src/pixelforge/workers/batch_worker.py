"""Toplu emal üçün thread-əsaslı işçi.

UI ilə əlaqə bir thread-safe `queue.Queue` üzərindən aparılır:
işçi emal hadisələrini növbəyə yazır, UI isə `after()` ilə müntəzəm
oxuyub vidcetləri yeniləyir.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable

from pixelforge.core.models import Job, JobStatus
from pixelforge.core.pipeline import process_job

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkerEvent:
    """UI-yə göndərilən bir hadisə."""

    kind: str            # "job_started" | "job_done" | "job_failed" | "batch_done" | "log"
    job_index: int = -1
    job: Job | None = None
    message: str = ""


class BatchWorker:
    """Toplu emal işini icra edən fon işçisi."""

    def __init__(self, max_workers: int = 2) -> None:
        self.max_workers = max(1, max_workers)
        self.events: queue.Queue[WorkerEvent] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._jobs: list[Job] = []

    @property
    def is_running(self) -> bool:
        """İşçi aktivdirsə True qaytarır."""
        return self._thread is not None and self._thread.is_alive()

    def start(self, jobs: list[Job], on_event: Callable[[WorkerEvent], None] | None = None) -> None:
        """Verilmiş işləri arxa fonda emal etməyə başlayır."""
        if self.is_running:
            logger.warning("İşçi artıq fəaldır — yeni başlatma rədd edildi")
            return
        self._jobs = jobs
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(on_event,),
            name="pixelforge-batch",
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        """Cari toplu emalı dayandırmağı tələb edir."""
        self._stop_event.set()

    def join(self, timeout: float | None = None) -> None:
        """İşçinin tamamlanmasını gözləyir."""
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _emit(self, event: WorkerEvent, callback: Callable[[WorkerEvent], None] | None) -> None:
        """Hadisəni növbəyə (və varsa, callback-ə) ötürür."""
        try:
            self.events.put_nowait(event)
        except queue.Full:
            pass
        if callback is not None:
            try:
                callback(event)
            except Exception:  # noqa: BLE001
                logger.exception("Hadisə callback-i xəta verdi")

    def _run(self, on_event: Callable[[WorkerEvent], None] | None) -> None:
        """Əsas icra döngüsü."""
        start_ts = time.perf_counter()
        total = len(self._jobs)
        logger.info("Toplu emal başladı: %d fayl, %d işçi", total, self.max_workers)

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {}
            for idx, job in enumerate(self._jobs):
                if self._stop_event.is_set():
                    break
                self._emit(
                    WorkerEvent(kind="job_started", job_index=idx, job=job),
                    on_event,
                )
                futures[pool.submit(process_job, job)] = idx

            for future in list(futures):
                if self._stop_event.is_set():
                    future.cancel()
                    continue
                idx = futures[future]
                try:
                    finished = future.result()
                except Exception as exc:  # noqa: BLE001
                    self._jobs[idx].status = JobStatus.FAILED
                    self._jobs[idx].error = str(exc)
                    self._emit(
                        WorkerEvent(
                            kind="job_failed",
                            job_index=idx,
                            job=self._jobs[idx],
                            message=str(exc),
                        ),
                        on_event,
                    )
                    continue

                kind = "job_done" if finished.status == JobStatus.DONE else "job_failed"
                self._emit(
                    WorkerEvent(kind=kind, job_index=idx, job=finished),
                    on_event,
                )

        elapsed = time.perf_counter() - start_ts
        logger.info("Toplu emal bitdi: %.2f saniyə", elapsed)
        self._emit(
            WorkerEvent(kind="batch_done", message=f"{elapsed:.2f}s"),
            on_event,
        )
