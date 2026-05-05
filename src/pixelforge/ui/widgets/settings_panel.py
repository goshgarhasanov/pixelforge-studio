"""Sağ tərəfdəki tənzimləmələr (inspector) paneli."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from pixelforge.core.models import (
    CompressionOptions,
    ConvertOptions,
    JobOptions,
    ResizeMode,
    ResizeOptions,
)
from pixelforge.i18n import t
from pixelforge.ui import theme
from pixelforge.utils.formats import SUPPORTED_OUTPUT_FORMATS

# UI etiketi → ResizeMode
_RESIZE_MAP: dict[str, ResizeMode] = {
    "resize.none": ResizeMode.NONE,
    "resize.pixels": ResizeMode.PIXELS,
    "resize.percent": ResizeMode.PERCENT,
    "resize.long_edge": ResizeMode.LONG_EDGE,
    "resize.short_edge": ResizeMode.SHORT_EDGE,
}


class SettingsPanel(ctk.CTkFrame):
    """Çevir / ölçü dəyişdir / sıxışdır parametrləri."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_start: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color=theme.DARK_BG_ELEVATED, corner_radius=theme.RADIUS_LG)
        self._on_start = on_start

        self.grid_columnconfigure(0, weight=1)

        # Başlıq.
        title = ctk.CTkLabel(
            self,
            text=t("nav.settings"),
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_TITLE, "bold"),
            text_color=theme.DARK_TEXT_PRIMARY,
        )
        title.grid(row=0, column=0, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_MD, theme.SPACE_SM))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=theme.SPACE_LG, pady=theme.SPACE_SM)
        body.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        row = 0

        # --- Çıxış formatı ---
        self._add_label(body, t("settings.format"), row)
        self._format_var = ctk.StringVar(value="JPG")
        fmt_menu = ctk.CTkOptionMenu(
            body,
            values=list(SUPPORTED_OUTPUT_FORMATS),
            variable=self._format_var,
            fg_color=theme.DARK_BG_BASE,
            button_color=theme.GRADIENT_INDIGO,
            button_hover_color=theme.GRADIENT_FUCHSIA,
        )
        fmt_menu.grid(row=row + 1, column=0, sticky="we", pady=(0, theme.SPACE_MD))
        row += 2

        # --- Ölçü rejimi ---
        self._add_label(body, t("settings.resize_mode"), row)
        self._resize_var = ctk.StringVar(value=t("resize.none"))
        resize_menu = ctk.CTkOptionMenu(
            body,
            values=[t(k) for k in _RESIZE_MAP],
            variable=self._resize_var,
            fg_color=theme.DARK_BG_BASE,
            button_color=theme.ACCENT_VIOLET,
            button_hover_color=theme.GRADIENT_FUCHSIA,
            command=lambda _v: self._on_resize_mode_changed(),
        )
        resize_menu.grid(row=row + 1, column=0, sticky="we", pady=(0, theme.SPACE_MD))
        row += 2

        # --- En × hündürlük ---
        self._dim_frame = ctk.CTkFrame(body, fg_color="transparent")
        self._dim_frame.grid(row=row, column=0, sticky="we", pady=(0, theme.SPACE_MD))
        self._dim_frame.grid_columnconfigure(0, weight=1)
        self._dim_frame.grid_columnconfigure(2, weight=1)
        self._width_var = ctk.StringVar(value="1920")
        self._height_var = ctk.StringVar(value="1080")
        self._width_entry = ctk.CTkEntry(
            self._dim_frame, textvariable=self._width_var, placeholder_text=t("settings.width")
        )
        self._width_entry.grid(row=0, column=0, sticky="we")
        ctk.CTkLabel(self._dim_frame, text="×", text_color=theme.DARK_TEXT_MUTED).grid(
            row=0, column=1, padx=theme.SPACE_SM
        )
        self._height_entry = ctk.CTkEntry(
            self._dim_frame, textvariable=self._height_var, placeholder_text=t("settings.height")
        )
        self._height_entry.grid(row=0, column=2, sticky="we")
        row += 1

        # --- Faiz girişi ---
        self._percent_var = ctk.StringVar(value="50")
        self._percent_entry = ctk.CTkEntry(
            body, textvariable=self._percent_var, placeholder_text=t("settings.percent")
        )
        self._percent_entry.grid(row=row, column=0, sticky="we", pady=(0, theme.SPACE_MD))
        row += 1

        # --- Hədəf ölçü ---
        self._add_label(body, t("settings.target_kb"), row)
        self._target_var = ctk.StringVar(value="200")
        target_entry = ctk.CTkEntry(body, textvariable=self._target_var)
        target_entry.grid(row=row + 1, column=0, sticky="we", pady=(0, theme.SPACE_MD))
        row += 2

        # --- Çıxış qovluğu ---
        self._add_label(body, t("settings.output_dir"), row)
        out_frame = ctk.CTkFrame(body, fg_color="transparent")
        out_frame.grid(row=row + 1, column=0, sticky="we", pady=(0, theme.SPACE_MD))
        out_frame.grid_columnconfigure(0, weight=1)
        self._output_var = ctk.StringVar(value="./output")
        out_entry = ctk.CTkEntry(out_frame, textvariable=self._output_var)
        out_entry.grid(row=0, column=0, sticky="we")
        ctk.CTkButton(
            out_frame,
            text="…",
            width=32,
            command=self._pick_output_dir,
            fg_color=theme.DARK_BG_BASE,
            hover_color=theme.DARK_BG_OVERLAY,
        ).grid(row=0, column=1, padx=(theme.SPACE_SM, 0))
        row += 2

        # --- Başla düyməsi (qradient hiss) ---
        start_btn = ctk.CTkButton(
            self,
            text=f"⚡  {t('btn.forge').upper()}",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_TITLE, "bold"),
            height=52,
            corner_radius=theme.RADIUS_MD,
            fg_color=theme.GRADIENT_FUCHSIA,
            hover_color=theme.GRADIENT_INDIGO,
            text_color="#FFFFFF",
            command=self._on_start,
        )
        start_btn.grid(row=2, column=0, sticky="we", padx=theme.SPACE_LG, pady=(theme.SPACE_SM, theme.SPACE_LG))

        self._on_resize_mode_changed()

    @staticmethod
    def _add_label(parent: ctk.CTkBaseClass, text: str, row: int) -> None:
        """Bir başlıq etiketi əlavə edir."""
        ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            font=ctk.CTkFont(theme.FONT_FAMILY, theme.FS_SMALL, "bold"),
            text_color=theme.DARK_TEXT_SECONDARY,
        ).grid(row=row, column=0, sticky="we", pady=(0, 4))

    def _on_resize_mode_changed(self) -> None:
        """Seçilmiş rejimə uyğun olaraq müvafiq giriş sahələrini göstərir."""
        mode = self._selected_resize_mode()
        if mode in (ResizeMode.PIXELS,):
            self._dim_frame.grid()
            self._percent_entry.grid_remove()
        elif mode in (ResizeMode.PERCENT, ResizeMode.LONG_EDGE, ResizeMode.SHORT_EDGE):
            self._dim_frame.grid_remove()
            self._percent_entry.grid()
        else:
            self._dim_frame.grid_remove()
            self._percent_entry.grid_remove()

    def _selected_resize_mode(self) -> ResizeMode:
        """UI etiketindən enum-a çevirir."""
        for key, mode in _RESIZE_MAP.items():
            if t(key) == self._resize_var.get():
                return mode
        return ResizeMode.NONE

    def _pick_output_dir(self) -> None:
        """İstifadəçidən qovluq seçməsini xahiş edir."""
        chosen = filedialog.askdirectory(title=t("settings.output_dir"))
        if chosen:
            self._output_var.set(chosen)

    def build_options(self) -> JobOptions:
        """Cari girişlərdən tam `JobOptions` qurur."""
        mode = self._selected_resize_mode()
        try:
            width = int(self._width_var.get())
        except ValueError:
            width = 1920
        try:
            height = int(self._height_var.get())
        except ValueError:
            height = 1080
        try:
            percent = float(self._percent_var.get())
        except ValueError:
            percent = 100.0
        try:
            target_kb = max(1, int(self._target_var.get()))
        except ValueError:
            target_kb = 200

        edge_pixels: int | None = None
        if mode in (ResizeMode.LONG_EDGE, ResizeMode.SHORT_EDGE):
            try:
                edge_pixels = int(self._percent_var.get())
            except ValueError:
                edge_pixels = 1920

        out_dir_str = self._output_var.get().strip()
        out_dir: Path | None = Path(out_dir_str).expanduser().resolve() if out_dir_str else None

        return JobOptions(
            convert=ConvertOptions(output_format=self._format_var.get()),
            resize=ResizeOptions(
                mode=mode,
                width=width,
                height=height,
                percent=percent,
                edge_pixels=edge_pixels,
            ),
            compress=CompressionOptions(target_kb=target_kb),
            output_dir=out_dir,
        )
