"""Müasir IDE/dev-console üslubunda canlı log paneli.

Xüsusiyyətlər:
  • Səviyyə əsaslı rəngləmə (DEBUG / INFO / WARNING / ERROR / CRITICAL).
  • Sətir nömrələri.
  • Filtr çubuğu — səviyyəyə görə süzgəc.
  • Axtarış sahəsi.
  • Avtomatik aşağı sürüşmə (sürüşdükdə dayanır).
  • Köçürmə düyməsi (bütün loglar buferə).
  • Ümumi qeyd sayğacı.
"""

from __future__ import annotations

import queue
import re
import tkinter as tk

import customtkinter as ctk

from pixelforge.i18n import t
from pixelforge.logger import get_ui_log_queue
from pixelforge.ui import theme

# Yeniləmə intervalı (millisaniyə).
POLL_INTERVAL_MS = 200
MAX_LINES = 5000

# Səviyyələr üçün rənglər (müasir terminal palitrasi).
LEVEL_COLORS: dict[str, str] = {
    "DEBUG": "#6B6B8A",     # boz
    "INFO": "#06B6D4",      # cyan
    "WARNING": "#FACC15",   # sunflower
    "ERROR": "#F43F5E",     # coral
    "CRITICAL": "#FF1F5A",  # parlaq qırmızı
}

LEVEL_BG: dict[str, str] = {
    "CRITICAL": "#3D0A1A",  # ərimə qırmızı arxa fon
}

LEVEL_PATTERN = re.compile(r"\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]")
TIMESTAMP_PATTERN = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d{3})")


class LogViewer(ctk.CTkFrame):
    """Müasir, rəngli, axtarışlı log konsolu."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color=theme.DARK_BG_ELEVATED, corner_radius=theme.RADIUS_LG)
        self._queue: queue.Queue[str] = get_ui_log_queue()
        self._line_count = 0
        self._total_count = 0
        self._auto_scroll = True
        self._level_filter: set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        self._search_term: str = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---- Başlıq sırası ----
        self._build_header()

        # ---- Filtr / axtarış sırası ----
        self._build_toolbar()

        # ---- Mətn sahəsi ----
        self._build_textbox()

        # Polling.
        self.after(POLL_INTERVAL_MS, self._poll)

    # ------------------------------------------------------------------
    # Quruluş
    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        """Üst başlıq + sayğac + təmizlə düyməsi."""
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_MD, 0))
        head.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            head,
            text="▸ " + t("logs.title"),
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_TITLE, "bold"),
            text_color=theme.DARK_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self._counter = ctk.CTkLabel(
            head,
            text="0 qeyd",
            anchor="e",
            font=ctk.CTkFont(theme.FONT_MONO, theme.FS_SMALL),
            text_color=theme.DARK_TEXT_MUTED,
        )
        self._counter.grid(row=0, column=1, sticky="e", padx=(0, theme.SPACE_MD))

        ctk.CTkButton(
            head,
            text="⧉  Köçür",
            width=80,
            height=28,
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            fg_color=theme.DARK_BG_BASE,
            hover_color=theme.DARK_BG_OVERLAY,
            text_color=theme.DARK_TEXT_SECONDARY,
            command=self._copy_all,
        ).grid(row=0, column=2, padx=(0, 4))

        ctk.CTkButton(
            head,
            text="✕  " + t("logs.clear"),
            width=110,
            height=28,
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            fg_color=theme.DARK_BG_BASE,
            hover_color=theme.STATUS_FAILED,
            text_color=theme.DARK_TEXT_SECONDARY,
            command=self.clear,
        ).grid(row=0, column=3)

    def _build_toolbar(self) -> None:
        """Filtr + axtarış sırası."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_SM, 0))
        bar.grid_columnconfigure(6, weight=1)

        # Səviyyə filtr düymələri.
        self._level_buttons: dict[str, ctk.CTkButton] = {}
        for col, lvl in enumerate(("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")):
            btn = ctk.CTkButton(
                bar,
                text=lvl,
                width=72,
                height=24,
                font=ctk.CTkFont(theme.FONT_MONO, 10, "bold"),
                fg_color=LEVEL_COLORS[lvl],
                hover_color=LEVEL_COLORS[lvl],
                text_color="#0B0B12" if lvl in ("INFO", "WARNING") else "#FFFFFF",
                corner_radius=theme.RADIUS_SM,
                command=lambda level=lvl: self._toggle_level(level),
            )
            btn.grid(row=0, column=col, padx=(0, 4))
            self._level_buttons[lvl] = btn

        # Axtarış sahəsi.
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_changed())
        search = ctk.CTkEntry(
            bar,
            textvariable=self._search_var,
            placeholder_text="🔍  Axtar…",
            height=26,
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL),
            fg_color=theme.DARK_BG_BASE,
            border_color=theme.DARK_BORDER,
            text_color=theme.DARK_TEXT_PRIMARY,
        )
        search.grid(row=0, column=6, sticky="we", padx=(theme.SPACE_MD, 0))

    def _build_textbox(self) -> None:
        """Loglar üçün rəngli mətn sahəsi (tk.Text — tag dəstəyi üçün)."""
        wrap = ctk.CTkFrame(
            self,
            fg_color=theme.DARK_BG_DEEPEST,
            corner_radius=theme.RADIUS_MD,
            border_width=1,
            border_color=theme.DARK_BORDER,
        )
        wrap.grid(row=2, column=0, sticky="nsew", padx=theme.SPACE_SM, pady=theme.SPACE_SM)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        # Sürüşdürmə çubuğu.
        scroll = ctk.CTkScrollbar(wrap)
        scroll.grid(row=0, column=1, sticky="ns")

        # Native tk.Text — CTkTextbox tag rəngləməni tam dəstəkləmir.
        self._text = tk.Text(
            wrap,
            wrap="none",
            font=(theme.FONT_MONO, theme.FS_SMALL),
            bg=theme.DARK_BG_DEEPEST,
            fg=theme.DARK_TEXT_PRIMARY,
            insertbackground=theme.DARK_TEXT_PRIMARY,
            selectbackground=theme.GRADIENT_INDIGO,
            selectforeground="#FFFFFF",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=theme.SPACE_SM,
            pady=theme.SPACE_SM,
            yscrollcommand=scroll.set,
            state="disabled",
        )
        self._text.grid(row=0, column=0, sticky="nsew")
        scroll.configure(command=self._text.yview)

        # Tag-ları konfiqurasiya edirik.
        self._text.tag_configure("lineno", foreground=theme.DARK_TEXT_MUTED)
        self._text.tag_configure("timestamp", foreground=theme.ACCENT_VIOLET)
        self._text.tag_configure("module", foreground=theme.DARK_TEXT_SECONDARY)
        for lvl, color in LEVEL_COLORS.items():
            cfg: dict[str, str] = {"foreground": color}
            if lvl in LEVEL_BG:
                cfg["background"] = LEVEL_BG[lvl]
            self._text.tag_configure(f"lvl_{lvl}", **cfg)
        self._text.tag_configure(
            "search_hit",
            background=theme.GRADIENT_AMBER,
            foreground="#0B0B12",
        )

        # Sürüşdürdükdə avto-scroll dayanır.
        self._text.bind("<MouseWheel>", lambda _e: self._set_auto_scroll(False))
        self._text.bind("<Button-4>", lambda _e: self._set_auto_scroll(False))
        self._text.bind("<Button-5>", lambda _e: self._set_auto_scroll(False))
        self._text.bind("<End>", lambda _e: self._set_auto_scroll(True))

    # ------------------------------------------------------------------
    # Hadisələr
    # ------------------------------------------------------------------
    def _toggle_level(self, level: str) -> None:
        """Səviyyə filtr düyməsini açıb-bağlayır."""
        if level in self._level_filter:
            self._level_filter.discard(level)
            self._level_buttons[level].configure(fg_color=theme.DARK_BG_BASE)
        else:
            self._level_filter.add(level)
            self._level_buttons[level].configure(fg_color=LEVEL_COLORS[level])

    def _on_search_changed(self) -> None:
        """Axtarış mətni dəyişəndə vurğuları yeniləyir."""
        self._search_term = self._search_var.get().strip().lower()
        self._refresh_search_highlight()

    def _refresh_search_highlight(self) -> None:
        """Bütün uyğun gələn parçaları sarı ilə vurğulayır."""
        self._text.tag_remove("search_hit", "1.0", "end")
        if not self._search_term:
            return
        idx = "1.0"
        length = len(self._search_term)
        while True:
            idx = self._text.search(self._search_term, idx, nocase=1, stopindex="end")
            if not idx:
                break
            end = f"{idx}+{length}c"
            self._text.tag_add("search_hit", idx, end)
            idx = end

    def _set_auto_scroll(self, value: bool) -> None:
        """Avto-scroll vəziyyətini dəyişir."""
        # Sürüşdürmə yuxarı qalxsa, avto-scroll dayanır; sona qayıtsa, qoşulur.
        try:
            first, last = self._text.yview()
            self._auto_scroll = value if last >= 0.95 else False
        except Exception:
            self._auto_scroll = value

    def _copy_all(self) -> None:
        """Bütün log mətnini sistem buferinə köçürür."""
        try:
            content = self._text.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(content)
        except Exception:  # pragma: no cover
            pass

    def clear(self) -> None:
        """Bütün logları silir."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")
        self._line_count = 0
        self._total_count = 0
        self._update_counter()

    # ------------------------------------------------------------------
    # Polling və qeyd əlavəsi
    # ------------------------------------------------------------------
    def _poll(self) -> None:
        """Növbədəki bütün gözləyən qeydləri oxuyur."""
        drained = 0
        try:
            while drained < 100:
                line = self._queue.get_nowait()
                self._append(line)
                drained += 1
        except queue.Empty:
            pass
        self.after(POLL_INTERVAL_MS, self._poll)

    def _append(self, raw: str) -> None:
        """Bir log sətrini səviyyəyə görə rənglə əlavə edir."""
        self._total_count += 1
        m = LEVEL_PATTERN.search(raw)
        level = m.group(1) if m else "INFO"

        # Filtr aktiv deyilsə, qeyd görünmür (lakin sayılır).
        if level not in self._level_filter:
            self._update_counter()
            return

        self._line_count += 1
        line_no = f"{self._line_count:>5}  "

        # Sətir nömrəsi və səviyyə üçün ayrı tag-lar.
        self._text.configure(state="normal")
        self._text.insert("end", line_no, ("lineno",))

        # Timestamp ayrı boyada vurğulanır.
        ts_match = TIMESTAMP_PATTERN.match(raw)
        if ts_match:
            self._text.insert("end", ts_match.group(1), ("timestamp",))
            rest = raw[ts_match.end():]
        else:
            rest = raw

        # Səviyyə teqi rənglənir.
        if m:
            before = rest[: m.start() - (len(raw) - len(rest))] if False else ""
            # Sadə yanaşma: mətn parçalarına bölmək yerinə bütün qalan mətnə uyğun tag tətbiq edirik.
            self._text.insert("end", rest + "\n", (f"lvl_{level}",))
        else:
            self._text.insert("end", rest + "\n", ("lvl_INFO",))

        # Maksimum sətir sayını saxlayırıq.
        if self._line_count > MAX_LINES:
            self._text.delete("1.0", "200.0")
            self._line_count -= 200

        if self._auto_scroll:
            self._text.see("end")

        self._text.configure(state="disabled")
        self._update_counter()

        if self._search_term:
            self._refresh_search_highlight()

    def _update_counter(self) -> None:
        """Sayğacı yeniləyir (toplam qeyd sayı + filtr göstərici)."""
        if len(self._level_filter) == 5:
            self._counter.configure(text=f"{self._total_count:,} qeyd")
        else:
            shown = self._line_count
            self._counter.configure(text=f"{shown:,} / {self._total_count:,} qeyd")
