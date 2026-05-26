"""
Виджет анимации броска кубиков на Canvas.
Рисует D6 классически (с точками), остальные типы — как многоугольники с числом.
"""
import random
import tkinter as tk
from typing import Callable, List, Optional


# Цветовая схема
DICE_BG = "#FFFFFF"
DICE_BG_DARK = "#2C3E50"
DICE_BORDER = "#34495E"
PIP_COLOR = "#2C3E50"
PIP_COLOR_DARK = "#ECF0F1"
TEXT_COLOR = "#2C3E50"
TEXT_COLOR_DARK = "#ECF0F1"


class DiceAnimation(tk.Frame):
    """
    Виджет, рисующий результаты последнего броска и проигрывающий
    короткую анимацию «прокручивания» граней.
    """

    def __init__(self, parent, dice_size: int = 80, dark_mode: bool = False):
        # parent может быть ttk.Frame (без опции -bg), поэтому подбираем фон через стиль
        bg = _safe_bg(parent, "#F5F5F5")
        super().__init__(parent, bg=bg)
        self.dice_size = dice_size
        self.dark_mode = dark_mode
        self.canvas = tk.Canvas(
            self,
            height=dice_size + 20,
            highlightthickness=0,
            bg=bg,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._anim_id: Optional[str] = None
        self._current_values: List[int] = []
        self._dice_type: str = "D6"

    # --------- Публичные методы ---------

    def show_values(self, values: List[int], dice_type: str = "D6") -> None:
        """Сразу показать конкретные значения (без анимации)."""
        self._stop_animation()
        self._current_values = list(values)
        self._dice_type = dice_type
        self._render()

    def animate_roll(
        self,
        final_values: List[int],
        dice_type: str = "D6",
        duration_ms: int = 600,
        on_complete: Optional[Callable] = None,
    ) -> None:
        """
        Анимация «броска»: ~10 быстрых кадров случайных граней,
        затем финальные значения.
        """
        self._stop_animation()
        self._dice_type = dice_type
        sides = _dice_sides(dice_type)
        frames = 10
        interval = max(20, duration_ms // frames)

        def frame(step: int):
            if step < frames:
                self._current_values = [random.randint(1, sides) for _ in final_values]
                self._render()
                self._anim_id = self.after(interval, lambda: frame(step + 1))
            else:
                self._current_values = list(final_values)
                self._render()
                self._anim_id = None
                if on_complete:
                    on_complete()

        frame(0)

    def set_dark_mode(self, dark: bool) -> None:
        """Сменить цветовую тему виджета."""
        self.dark_mode = dark
        new_bg = "#2C3E50" if dark else "#FFFFFF"
        self.configure(bg=new_bg)
        self.canvas.configure(bg=new_bg)
        self._render()

    # --------- Внутреннее ---------

    def _stop_animation(self):
        if self._anim_id is not None:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

    def _render(self):
        """Перерисовать кубики на canvas."""
        c = self.canvas
        c.delete("all")
        size = self.dice_size
        padding = 12
        n = len(self._current_values)
        if n == 0:
            return

        # Достаточно широкий холст
        total_width = n * size + (n + 1) * padding
        c.configure(width=total_width)

        bg_color = DICE_BG_DARK if self.dark_mode else DICE_BG
        pip_color = PIP_COLOR_DARK if self.dark_mode else PIP_COLOR
        text_color = TEXT_COLOR_DARK if self.dark_mode else TEXT_COLOR

        x = padding
        y = 10
        for value in self._current_values:
            self._draw_die(c, x, y, size, value, bg_color, pip_color, text_color)
            x += size + padding

    def _draw_die(self, c, x, y, size, value, bg, pip, text):
        """Нарисовать один кубик."""
        # Скруглённый квадрат — имитируем овалом по углам + прямоугольником
        r = size * 0.18
        # для D6 рисуем точки, для остальных — число
        c.create_rectangle(
            x, y, x + size, y + size,
            fill=bg, outline=DICE_BORDER, width=2
        )
        if self._dice_type == "D6":
            self._draw_pips(c, x, y, size, value, pip)
        else:
            # многоугольник внутри + число
            cx = x + size / 2
            cy = y + size / 2
            font_size = max(10, int(size * 0.4))
            c.create_text(
                cx, cy,
                text=str(value),
                fill=text,
                font=("Helvetica", font_size, "bold"),
            )
            c.create_text(
                x + size - 14, y + 12,
                text=self._dice_type,
                fill=text,
                font=("Helvetica", max(7, int(size * 0.13))),
            )

    def _draw_pips(self, c, x, y, size, value, color):
        """Нарисовать точки на грани D6."""
        # Позиции в относительных координатах (0..1)
        positions = {
            1: [(0.5, 0.5)],
            2: [(0.25, 0.25), (0.75, 0.75)],
            3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
            4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
            5: [
                (0.25, 0.25), (0.75, 0.25),
                (0.5, 0.5),
                (0.25, 0.75), (0.75, 0.75),
            ],
            6: [
                (0.25, 0.25), (0.75, 0.25),
                (0.25, 0.5), (0.75, 0.5),
                (0.25, 0.75), (0.75, 0.75),
            ],
        }
        pips = positions.get(value, [])
        radius = max(3, size * 0.07)
        for px, py in pips:
            cx = x + px * size
            cy = y + py * size
            c.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill=color, outline=""
            )


def _dice_sides(dice_type: str) -> int:
    """Вернуть число граней по строковому типу."""
    from game_logic.dice import DICE_TYPES
    return DICE_TYPES.get(dice_type, 6)


def _safe_bg(widget, default: str) -> str:
    """Безопасно получить цвет фона у любого виджета (tk или ttk)."""
    try:
        bg = widget.cget("background")
        if bg:
            return bg
    except tk.TclError:
        pass
    try:
        import tkinter.ttk as ttk
        style = ttk.Style()
        bg = style.lookup("TFrame", "background")
        if bg:
            return bg
    except Exception:
        pass
    return default
