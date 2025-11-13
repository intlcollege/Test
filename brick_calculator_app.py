"""Graphical brick, discount, and national ID utilities.

This module exposes :class:`BrickCalculatorApp`, a polished Tkinter application that
combines several handy calculators for a masonry business.  The UI is entirely
localized in Persian.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import partial
from typing import Iterable, Sequence

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


# ---------------------------------------------------------------------------
# Configuration data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StylePalette:
    """Color and font palette for the widgets."""

    base_font: tuple[str, int] = ("Tahoma", 11)
    header_font: tuple[str, int, str] = ("Tahoma", 14, "bold")
    button_font: tuple[str, int, str] = ("Tahoma", 12, "bold")
    text_color: str = "#333"
    accent_color: str = "#0078D7"
    accent_color_active: str = "#005A9E"
    header_color: str = "#00529B"


@dataclass(frozen=True)
class WallPattern:
    """Represents a brick wall pattern multiplier."""

    label: str
    multiplier: float


WALL_PATTERNS: tuple[WallPattern, ...] = (
    WallPattern("دیوار ۱۰ سانتی (یک ردیفه)", 1.0),
    WallPattern("دیوار ۲۰ سانتی (دو ردیفه)", 2.0),
    WallPattern("دیوار ۳۵ سانتی (یک و نیم آجره)", 3.0),
)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def configure_style(root: tk.Tk, palette: StylePalette) -> None:
    """Apply a consistent style to the Tkinter widgets."""

    style = ttk.Style(root)
    style.theme_use("vista")
    style.configure(".", font=palette.base_font, padding=5)
    style.configure("TLabel", foreground=palette.text_color)
    style.configure("Header.TLabel", font=palette.header_font, foreground=palette.header_color)
    style.configure(
        "TButton",
        font=palette.button_font,
        foreground="white",
        background=palette.accent_color,
    )
    style.map("TButton", background=[("active", palette.accent_color_active)])


def create_label_frame(parent: tk.Widget, text: str) -> ttk.LabelFrame:
    """Create a consistently styled ``LabelFrame``."""

    frame = ttk.LabelFrame(parent, text=f" {text} ", padding="15 10")
    frame.pack(fill=tk.X, pady=5)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    return frame


def make_labeled_entry(
    parent: ttk.LabelFrame,
    label: str,
    textvariable: tk.StringVar,
    row: int,
    justify: str = "right",
) -> ttk.Entry:
    """Create a label and entry pair on a grid row."""

    ttk.Label(parent, text=label).grid(row=row, column=1, sticky="e", padx=(0, 10), pady=5)
    entry = ttk.Entry(parent, textvariable=textvariable, width=25, justify=justify, font=("Tahoma", 11))
    entry.grid(row=row, column=0, sticky="ew", pady=5)
    return entry


def make_labeled_combobox(
    parent: ttk.LabelFrame,
    label: str,
    textvariable: tk.StringVar,
    values: Sequence[str],
    row: int,
) -> ttk.Combobox:
    """Create a label and combobox pair on a grid row."""

    ttk.Label(parent, text=label).grid(row=row, column=1, sticky="e", padx=(0, 10), pady=5)
    combo = ttk.Combobox(parent, textvariable=textvariable, values=list(values), state="readonly", justify="right", font=("Tahoma", 11))
    combo.grid(row=row, column=0, sticky="ew", pady=5)
    if values:
        combo.current(0)
    return combo


def enforce_numeric_format(
    var: tk.StringVar,
    entry: ttk.Entry,
    flag_container: dict[str, bool],
    flag_key: str,
) -> None:
    """Format a StringVar with thousands separators while preserving cursor position."""

    if flag_container.get(flag_key):
        return

    flag_container[flag_key] = True
    current_value = var.get()
    digits = "".join(filter(str.isdigit, current_value))

    if digits:
        formatted_value = f"{int(digits):,}"
        if formatted_value != current_value:
            var.set(formatted_value)
            entry.after_idle(partial(entry.icursor, tk.END))

    flag_container[flag_key] = False


def show_report(root: tk.Tk, title: str, rows: Iterable[tuple[str, str, bool]]) -> None:
    """Render a modal window containing calculated results."""

    report_win = tk.Toplevel(root)
    report_win.title(title)
    report_win.geometry("460x320")
    report_win.resizable(False, False)
    report_win.transient(root)
    report_win.grab_set()

    main_frame = ttk.Frame(report_win, padding="15")
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text=title, style="Header.TLabel", anchor="center").pack(fill="x", pady=(0, 15))

    results_frame = ttk.Frame(main_frame)
    results_frame.pack(fill="x", expand=True)
    results_frame.columnconfigure(0, weight=1)
    results_frame.columnconfigure(1, weight=1)

    for row_index, (label, value, highlight) in enumerate(rows):
        value_font = ("Tahoma", 11, "bold")
        value_color = "#0078D7" if highlight else "#333"

        ttk.Label(results_frame, text=label, anchor="e").grid(row=row_index, column=1, sticky="e", pady=5, padx=(0, 10))
        ttk.Label(results_frame, text=value, anchor="w", font=value_font, foreground=value_color).grid(
            row=row_index,
            column=0,
            sticky="w",
            pady=5,
        )

    ttk.Button(main_frame, text="بستن", command=report_win.destroy, style="TButton").pack(side="bottom", pady=(15, 0))


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------


class BrickCalculatorApp(tk.Tk):
    """Main application window housing three distinct calculators."""

    waste_default = "7"
    joint_default = "1.5"
    vat_default = "10"

    def __init__(self) -> None:
        super().__init__()
        self._formatting_flags: dict[str, bool] = {}

        # Window configuration
        self.title("شرکت آجر سفال خوش رنگ میبد")
        self.geometry("620x660")
        self.resizable(False, False)

        configure_style(self, StylePalette())
        self._build_layout()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)

        tabs = {
            "about": ttk.Frame(notebook, padding="10"),
            "brick": ttk.Frame(notebook, padding="10"),
            "discount": ttk.Frame(notebook, padding="10"),
            "nid": ttk.Frame(notebook, padding="10"),
        }

        notebook.add(tabs["about"], text="توسعه دهنده")
        notebook.add(tabs["brick"], text="محاسبه‌گر آجر نما")
        notebook.add(tabs["discount"], text="محاسبه‌گر تخفیف")
        notebook.add(tabs["nid"], text="درست سنجی کد ملی")

        self._populate_about_tab(tabs["about"])
        self._populate_brick_tab(tabs["brick"])
        self._populate_discount_tab(tabs["discount"])
        self._populate_nid_tab(tabs["nid"])

    def _populate_brick_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="محاسبه‌گر آجر نما", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(0, 20))

        wall_frame = create_label_frame(parent, "مشخصات دیوار (متر)")
        brick_frame = create_label_frame(parent, "مشخصات آجر و بندکشی (سانتی‌متر)")

        self.wall_width = tk.StringVar()
        self.wall_height = tk.StringVar()
        self.wall_pattern = tk.StringVar()
        self.brick_length = tk.StringVar()
        self.brick_height = tk.StringVar()
        self.joint_thickness = tk.StringVar(value=self.joint_default)
        self.waste_percentage = tk.StringVar(value=self.waste_default)

        make_labeled_entry(wall_frame, "عرض دیوار‏:", self.wall_width, 0)
        make_labeled_entry(wall_frame, "ارتفاع دیوار‏:", self.wall_height, 1)
        make_labeled_combobox(
            wall_frame,
            "نحوه چیدمان دیوار‏:",
            self.wall_pattern,
            [pattern.label for pattern in WALL_PATTERNS],
            2,
        )

        make_labeled_entry(brick_frame, "طول آجر‏:", self.brick_length, 0)
        make_labeled_entry(brick_frame, "ارتفاع (ضخامت) آجر‏:", self.brick_height, 1)
        make_labeled_entry(brick_frame, "ضخامت بندکشی‏:", self.joint_thickness, 2)
        make_labeled_entry(brick_frame, "درصد پرتی و شکستگی‏:", self.waste_percentage, 3)

        ttk.Button(parent, text="محاسبه کن", command=self.perform_calculation).pack(pady=(25, 15), ipady=10, fill=tk.X)
        ttk.Label(parent, text="نتیجه در یک پنجره جدید نمایش داده خواهد شد.", anchor="center").pack(pady=5)

    def _populate_nid_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="اعتبارسنجی کد ملی ایران", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(0, 20))

        self.nid_var = tk.StringVar()
        ttk.Label(parent, text="کد ملی ۱۰ رقمی را بدون خط تیره وارد کنید‏:", anchor="center").pack(pady=(10, 5))

        entry = ttk.Entry(parent, textvariable=self.nid_var, width=30, justify="center", font=("Tahoma", 14))
        entry.pack(pady=10, ipady=5)

        ttk.Button(parent, text="بررسی کن", command=self.validate_nid).pack(pady=20, ipady=10, ipadx=30)
        self.nid_result_label = ttk.Label(parent, text="نتیجه در اینجا نمایش داده می‌شود.", font=("Tahoma", 12, "bold"), anchor="center")
        self.nid_result_label.pack(pady=10, fill=tk.X)

    def _populate_discount_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="مهندسی معکوس تخفیف", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(0, 20))

        input_frame = create_label_frame(parent, "اطلاعات فاکتور")

        self.original_price = tk.StringVar()
        self.vat_percentage = tk.StringVar(value=self.vat_default)
        self.final_price = tk.StringVar()

        original_entry = make_labeled_entry(input_frame, "قیمت کل اولیه (بدون ارزش افزوده)‏:", self.original_price, 0)
        make_labeled_entry(input_frame, "درصد ارزش افزوده (%)‏:", self.vat_percentage, 1)
        final_entry = make_labeled_entry(input_frame, "مبلغ نهایی پرداختی (توافقی)‏:", self.final_price, 2)

        self.original_price.trace_add(
            "write",
            lambda *_: enforce_numeric_format(self.original_price, original_entry, self._formatting_flags, "original"),
        )
        self.final_price.trace_add(
            "write",
            lambda *_: enforce_numeric_format(self.final_price, final_entry, self._formatting_flags, "final"),
        )

        ttk.Button(parent, text="محاسبه تخفیف", command=self.calculate_reverse_discount).pack(pady=(25, 15), ipady=10, fill=tk.X)
        ttk.Label(parent, text="نتیجه در یک پنجره جدید نمایش داده خواهد شد.", anchor="center").pack(pady=5)

    def _populate_about_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="توسعه دهنده", style="Header.TLabel", anchor="center").pack(fill=tk.X, pady=(20, 30))
        ttk.Label(parent, text="جواد خلیفه مهرجردی", font=("Tahoma", 16, "bold"), anchor="center").pack(pady=10)
        ttk.Label(parent, text="شماره همراه‏: 09132534542", font=("Tahoma", 14), anchor="center").pack(pady=5)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def perform_calculation(self) -> None:
        """Calculate the required number of bricks for the given wall."""

        try:
            wall_w = self._parse_positive_float(self.wall_width.get(), "عرض دیوار")
            wall_h = self._parse_positive_float(self.wall_height.get(), "ارتفاع دیوار")
            brick_l = self._parse_positive_float(self.brick_length.get(), "طول آجر")
            brick_h = self._parse_positive_float(self.brick_height.get(), "ارتفاع آجر")
            joint_t = self._parse_non_negative_float(self.joint_thickness.get(), "ضخامت بندکشی")
            waste = self._parse_non_negative_float(self.waste_percentage.get(), "درصد پرتی")

            selected_pattern = next((pattern for pattern in WALL_PATTERNS if pattern.label == self.wall_pattern.get()), WALL_PATTERNS[0])

            wall_area = wall_w * wall_h
            joint_m = joint_t / 100.0
            brick_area = ((brick_l / 100.0) + joint_m) * ((brick_h / 100.0) + joint_m)

            if brick_area == 0:
                raise ZeroDivisionError

            bricks_needed = math.ceil((wall_area / brick_area) * selected_pattern.multiplier)
            total_bricks = math.ceil(bricks_needed * (1 + waste / 100.0))

            show_report(
                self,
                "گزارش محاسبه آجر نما",
                (
                    ("مساحت کل دیوار:", f"{wall_area:,.2f} متر مربع", False),
                    ("نوع چیدمان دیوار:", selected_pattern.label, False),
                    ("تعداد آجر خالص:", f"{bricks_needed:,} عدد", False),
                    (f"تعداد کل با {waste:g}% پرتی:", f"{total_bricks:,} عدد", True),
                ),
            )
        except ValueError as exc:
            messagebox.showerror("خطای ورودی", str(exc))
        except ZeroDivisionError:
            messagebox.showerror("خطای محاسبه", "ابعاد آجر نمی‌تواند صفر باشد.")

    def validate_nid(self) -> None:
        """Validate an Iranian national ID and update the result label."""

        nid = self.nid_var.get().strip()
        if not (nid.isdigit() and len(nid) == 10):
            self.nid_result_label.config(text="کد ملی باید ۱۰ رقم و فقط شامل اعداد باشد.", foreground="red")
            return

        digits = [int(char) for char in nid]
        checksum = digits[-1]
        weighted_sum = sum(digit * (10 - index) for index, digit in enumerate(digits[:-1]))
        remainder = weighted_sum % 11
        is_valid = (remainder < 2 and checksum == remainder) or (remainder >= 2 and checksum == 11 - remainder)

        if is_valid:
            self.nid_result_label.config(text="کد ملی وارد شده معتبر است.", foreground="green")
        else:
            self.nid_result_label.config(text="کد ملی وارد شده نامعتبر است.", foreground="red")

    def calculate_reverse_discount(self) -> None:
        """Reverse engineer the discount applied to a final price."""

        try:
            original_p = self._parse_positive_float(self.original_price.get().replace(",", ""), "قیمت کل اولیه")
            vat_p = self._parse_non_negative_float(self.vat_percentage.get(), "درصد ارزش افزوده")
            final_p = self._parse_positive_float(self.final_price.get().replace(",", ""), "مبلغ نهایی")

            vat_rate = vat_p / 100.0
            new_base_price = final_p / (1 + vat_rate)
            discount_amount = original_p - new_base_price
            discount_percentage = (discount_amount / original_p) * 100

            show_report(
                self,
                "گزارش مهندسی معکوس تخفیف",
                (
                    ("قیمت کل اولیه:", f"{original_p:,.0f} ریال", False),
                    ("مبلغ نهایی پرداختی:", f"{final_p:,.0f} ریال", False),
                    ("مبلغ تخفیف اعمال شده:", f"{discount_amount:,.0f} ریال", True),
                    ("درصد تخفیف معادل:", f"{discount_percentage:.2f} %", True),
                ),
            )
        except ValueError as exc:
            messagebox.showerror("خطای ورودی", str(exc))

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_positive_float(value: str, field_name: str) -> float:
        number = float(value.strip())
        if number <= 0:
            raise ValueError(f"{field_name} باید مقدار مثبت داشته باشد.")
        return number

    @staticmethod
    def _parse_non_negative_float(value: str, field_name: str) -> float:
        number = float(value.strip())
        if number < 0:
            raise ValueError(f"{field_name} نمی‌تواند منفی باشد.")
        return number


if __name__ == "__main__":
    app = BrickCalculatorApp()
    app.mainloop()
