"""
Вкладка «Статистика» — гистограммы, теория vs практика, тепловые карты.
Использует matplotlib (с backend TkAgg).
"""
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from game_logic.dice import DICE_TYPES
from game_logic.probability import (
    sum_distribution,
    expected_sum,
    std_sum,
    probability_at_least,
    probability_at_most,
    probability_equals,
    probability_in_range,
    chi_square_test,
)
from utils.statistics import basic_stats


class StatsTab(ttk.Frame):
    """Вкладка статистики и анализа."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Левая колонка: калькулятор вероятностей и базовая статистика
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        calc_frame = ttk.LabelFrame(left, text="Калькулятор вероятностей", padding=10)
        calc_frame.pack(fill=tk.X)

        ttk.Label(calc_frame, text="Кубик:").grid(row=0, column=0, sticky="w")
        self.dice_type_var = tk.StringVar(value="D6")
        ttk.Combobox(
            calc_frame, textvariable=self.dice_type_var,
            values=list(DICE_TYPES.keys()), state="readonly", width=6,
        ).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(calc_frame, text="Кол-во:").grid(row=1, column=0, sticky="w")
        self.num_dice_var = tk.IntVar(value=3)
        ttk.Spinbox(
            calc_frame, from_=1, to=20, textvariable=self.num_dice_var, width=6
        ).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(calc_frame, text="Условие:").grid(row=2, column=0, sticky="w")
        self.condition_var = tk.StringVar(value=">=")
        ttk.Combobox(
            calc_frame, textvariable=self.condition_var,
            values=[">=", "<=", "=", "between"],
            state="readonly", width=8,
        ).grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(calc_frame, text="Значение(я):").grid(row=3, column=0, sticky="w")
        self.value_var = tk.StringVar(value="15")
        ttk.Entry(calc_frame, textvariable=self.value_var, width=10).grid(
            row=3, column=1, padx=5, pady=2
        )
        ttk.Label(
            calc_frame,
            text="(для between через дефис: 10-15)",
            font=("Helvetica", 8),
            foreground="#555",
        ).grid(row=4, column=0, columnspan=2, sticky="w")

        ttk.Button(
            calc_frame, text="Рассчитать", command=self.calculate_probability
        ).grid(row=5, column=0, columnspan=2, pady=5, sticky="we")

        self.calc_result = ttk.Label(
            calc_frame, text="—", font=("Helvetica", 11, "bold"),
            wraplength=240, justify="left"
        )
        self.calc_result.grid(row=6, column=0, columnspan=2, pady=5)

        # Теоретические показатели
        info = ttk.LabelFrame(left, text="Теория", padding=10)
        info.pack(fill=tk.X, pady=10)
        self.theory_label = ttk.Label(info, text="—", justify="left")
        self.theory_label.pack(anchor="w")
        ttk.Button(info, text="Обновить", command=self._update_theory).pack(
            anchor="e", pady=(5, 0)
        )

        # Чи-квадрат тест
        chi_frame = ttk.LabelFrame(left, text="Проверка случайности", padding=10)
        chi_frame.pack(fill=tk.X, pady=10)
        self.chi_label = ttk.Label(chi_frame, text="—", justify="left", wraplength=240)
        self.chi_label.pack(anchor="w")
        ttk.Button(
            chi_frame, text="Проверить текущую игру", command=self.run_chi_square
        ).pack(anchor="e", pady=(5, 0))

        # Правая колонка: графики
        right = ttk.Frame(self)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        chart_btns = ttk.Frame(right)
        chart_btns.pack(fill=tk.X)
        ttk.Button(
            chart_btns, text="Гистограмма выпавших значений",
            command=self.plot_histogram
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            chart_btns, text="Теория vs практика",
            command=self.plot_theory_vs_practice
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            chart_btns, text="Сравнение игроков",
            command=self.plot_player_comparison
        ).pack(side=tk.LEFT, padx=5)

        self.fig = Figure(figsize=(6, 4.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)

        # Базовая статистика
        stats_frame = ttk.LabelFrame(right, text="Сводная статистика по сессии", padding=10)
        stats_frame.pack(fill=tk.X)
        self.stats_label = ttk.Label(stats_frame, text="—", justify="left")
        self.stats_label.pack(anchor="w")

        self._update_theory()

    # ---------- Калькулятор ----------

    def calculate_probability(self):
        try:
            dice_type = self.dice_type_var.get()
            num_dice = self.num_dice_var.get()
            cond = self.condition_var.get()
            val_str = self.value_var.get().strip()

            if cond == "between":
                if "-" not in val_str:
                    raise ValueError("Для between введите две границы через дефис, например 10-15")
                low_s, high_s = val_str.split("-", 1)
                low, high = int(low_s), int(high_s)
                p = probability_in_range(low, high, num_dice, dice_type)
                text = f"P({low} ≤ сумма ≤ {high}) = {p:.4f} ({p*100:.2f}%)"
            else:
                val = int(val_str)
                if cond == ">=":
                    p = probability_at_least(val, num_dice, dice_type)
                    text = f"P(сумма ≥ {val}) = {p:.4f} ({p*100:.2f}%)"
                elif cond == "<=":
                    p = probability_at_most(val, num_dice, dice_type)
                    text = f"P(сумма ≤ {val}) = {p:.4f} ({p*100:.2f}%)"
                else:  # "="
                    p = probability_equals(val, num_dice, dice_type)
                    text = f"P(сумма = {val}) = {p:.4f} ({p*100:.2f}%)"
            self.calc_result.configure(text=text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Невалидный ввод: {e}")

    # ---------- Теория ----------

    def _update_theory(self):
        dice_type = self.dice_type_var.get()
        num_dice = self.num_dice_var.get()
        try:
            mean = expected_sum(num_dice, dice_type)
            std = std_sum(num_dice, dice_type)
            sides = DICE_TYPES[dice_type]
            text = (
                f"Кубики: {num_dice}×{dice_type}\n"
                f"Диапазон суммы: {num_dice}…{num_dice * sides}\n"
                f"Мат. ожидание (μ) = {mean:.2f}\n"
                f"Станд. отклонение (σ) = {std:.2f}\n"
                f"Дисперсия (σ²) = {std**2:.2f}"
            )
            self.theory_label.configure(text=text)
        except Exception as e:
            self.theory_label.configure(text=f"Ошибка: {e}")

    # ---------- Чи-квадрат ----------

    def run_chi_square(self):
        game = self.controller.game
        if game is None or not game.dice_roller.history:
            messagebox.showinfo("Информация", "Нет данных для анализа")
            return
        # Берём все броски одного типа (самого популярного)
        from collections import Counter
        type_counter = Counter(
            (r.num_dice, r.dice_type) for r in game.dice_roller.history
        )
        most_common = type_counter.most_common(1)[0][0]
        num_dice, dice_type = most_common
        sums = [
            sum(r.values) for r in game.dice_roller.history
            if r.num_dice == num_dice and r.dice_type == dice_type
        ]
        chi2, df = chi_square_test(sums, num_dice, dice_type)
        self.chi_label.configure(
            text=(
                f"Тип: {num_dice}×{dice_type}\n"
                f"Бросков: {len(sums)}\n"
                f"χ² = {chi2:.3f}, df = {df}\n"
                "Чем меньше χ², тем ближе результаты к теоретическому распределению."
            )
        )

    # ---------- Графики ----------

    def _all_values(self):
        game = self.controller.game
        if game is None:
            return []
        return game.dice_roller.all_values()

    def plot_histogram(self):
        values = self._all_values()
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        if not values:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
            self.canvas.draw()
            return
        sides_max = max(values)
        bins = np.arange(0.5, sides_max + 1.5, 1)
        ax.hist(values, bins=bins, color="#3498DB", edgecolor="#2C3E50")
        ax.set_xticks(range(1, sides_max + 1))
        ax.set_xlabel("Выпавшее значение")
        ax.set_ylabel("Частота")
        ax.set_title("Гистограмма выпавших значений (все кубики)")
        ax.grid(axis="y", alpha=0.3)
        self.fig.tight_layout()
        self.canvas.draw()
        self._update_stats_summary(values)

    def plot_theory_vs_practice(self):
        game = self.controller.game
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        if game is None or not game.dice_roller.history:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
            self.canvas.draw()
            return

        # Берём самый частый формат броска
        from collections import Counter
        type_counter = Counter(
            (r.num_dice, r.dice_type) for r in game.dice_roller.history
        )
        (num_dice, dice_type), _ = type_counter.most_common(1)[0]
        sums = [
            sum(r.values) for r in game.dice_roller.history
            if r.num_dice == num_dice and r.dice_type == dice_type
        ]
        n = len(sums)
        if n == 0:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
            self.canvas.draw()
            return

        theory = sum_distribution(num_dice, DICE_TYPES[dice_type])
        sums_range = sorted(theory.keys())
        theory_counts = [theory[s] * n for s in sums_range]

        observed_counter = Counter(sums)
        observed_counts = [observed_counter.get(s, 0) for s in sums_range]

        x = np.arange(len(sums_range))
        width = 0.4
        ax.bar(x - width/2, theory_counts, width, label="Теория", color="#95A5A6")
        ax.bar(x + width/2, observed_counts, width, label="Факт", color="#E74C3C")
        ax.set_xticks(x)
        ax.set_xticklabels(sums_range, rotation=45 if len(sums_range) > 12 else 0)
        ax.set_xlabel(f"Сумма {num_dice}{dice_type}")
        ax.set_ylabel("Количество появлений")
        ax.set_title(f"Теория vs практика ({n} бросков)")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        self.fig.tight_layout()
        self.canvas.draw()
        self._update_stats_summary(sums)

    def plot_player_comparison(self):
        game = self.controller.game
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        if game is None or not game.players:
            ax.text(0.5, 0.5, "Нет игроков", ha="center", va="center")
            self.canvas.draw()
            return
        names = [p.name for p in game.players]
        scores = [p.score for p in game.players]
        colors = [p.color for p in game.players]
        ax.bar(names, scores, color=colors, edgecolor="#2C3E50")
        ax.set_ylabel("Очки")
        ax.set_title("Текущие очки игроков")
        ax.grid(axis="y", alpha=0.3)
        for i, s in enumerate(scores):
            ax.text(i, s, f" {s}", ha="center", va="bottom")
        self.fig.tight_layout()
        self.canvas.draw()

    def _update_stats_summary(self, values):
        stats = basic_stats(values)
        text = (
            f"n={stats['count']}  "
            f"mean={stats['mean']:.2f}  "
            f"std={stats['std']:.2f}  "
            f"min={stats['min']}  "
            f"max={stats['max']}  "
            f"median={stats['median']:.1f}"
        )
        self.stats_label.configure(text=text)

    # ---------- Контроллер обновляет ----------

    def update_from_game(self):
        """Перерисовать гистограмму при обновлении."""
        # Не перерисовываем автоматически чтобы не дёргать пользователя,
        # но если уже отображалась — обновим.
        if self.fig.get_axes():
            try:
                self.plot_histogram()
            except Exception:
                pass
