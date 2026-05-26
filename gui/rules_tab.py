"""
Вкладка «Правила» — выбор пресета и настройка целевых очков.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from game_logic.dice import DICE_TYPES
from presets import (
    PRESET_GAMES,
    FiveThousandRules,
    PokerDiceRules,
    CustomGameRules,
)
from presets.custom_game import CustomGameConfig


class RulesTab(ttk.Frame):
    """Вкладка настройки правил."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        top = ttk.LabelFrame(self, text="Выберите игру", padding=10)
        top.pack(fill=tk.X, padx=10, pady=10)

        self.game_type_var = tk.StringVar(value="five_thousand")
        for key, cls in PRESET_GAMES.items():
            label = cls.name
            ttk.Radiobutton(
                top, text=label, value=key, variable=self.game_type_var,
                command=self._on_game_changed,
            ).pack(anchor="w")

        # Описание
        desc_frame = ttk.LabelFrame(self, text="Описание", padding=10)
        desc_frame.pack(fill=tk.X, padx=10, pady=5)
        self.desc_label = ttk.Label(desc_frame, text="", wraplength=600, justify="left")
        self.desc_label.pack(anchor="w")

        # Целевые очки и общие параметры
        common = ttk.LabelFrame(self, text="Параметры", padding=10)
        common.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(common, text="Целевые очки:").grid(row=0, column=0, sticky="w")
        self.target_var = tk.IntVar(value=5000)
        ttk.Spinbox(
            common, from_=10, to=100000, increment=100,
            textvariable=self.target_var, width=10
        ).grid(row=0, column=1, padx=5)

        # Параметры для CUSTOM
        self.custom_frame = ttk.LabelFrame(self, text="Параметры настраиваемой игры", padding=10)
        # отображается, только когда выбран custom

        ttk.Label(self.custom_frame, text="Тип кубика:").grid(row=0, column=0, sticky="w")
        self.custom_dice_type_var = tk.StringVar(value="D6")
        ttk.Combobox(
            self.custom_frame, textvariable=self.custom_dice_type_var,
            values=list(DICE_TYPES.keys()), state="readonly", width=6
        ).grid(row=0, column=1, padx=5)

        ttk.Label(self.custom_frame, text="Кол-во кубиков:").grid(row=1, column=0, sticky="w")
        self.custom_num_dice_var = tk.IntVar(value=2)
        ttk.Spinbox(
            self.custom_frame, from_=1, to=20,
            textvariable=self.custom_num_dice_var, width=6
        ).grid(row=1, column=1, padx=5)

        self.base_sum_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.custom_frame,
            text="Базовые очки = сумма броска",
            variable=self.base_sum_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

        ttk.Label(
            self.custom_frame,
            text="Бонусы за одинаковые кубики (формат: N:бонус через запятую)\nНапример: 3:50, 4:150, 5:300",
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.bonuses_var = tk.StringVar(value="3:50, 4:150, 5:300")
        ttk.Entry(self.custom_frame, textvariable=self.bonuses_var, width=40).grid(
            row=4, column=0, columnspan=2, sticky="we", padx=5, pady=2
        )

        ttk.Label(
            self.custom_frame,
            text="Штрафы за значения (формат: значение:штраф через запятую)\nНапример: 1:10  — каждая «1» отнимает 10 очков",
            justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.penalties_var = tk.StringVar(value="")
        ttk.Entry(self.custom_frame, textvariable=self.penalties_var, width=40).grid(
            row=6, column=0, columnspan=2, sticky="we", padx=5, pady=2
        )

        # Кнопки применить
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=10, pady=15)

        ttk.Button(
            btns, text="✓ Создать новую игру с этими правилами",
            command=self.apply_rules
        ).pack(side=tk.LEFT)

        self._on_game_changed()

    def _on_game_changed(self):
        gt = self.game_type_var.get()
        cls = PRESET_GAMES[gt]
        self.desc_label.configure(text=cls.description)

        # Дефолтное target_score
        defaults = {
            "five_thousand": 5000,
            "poker_dice": 1000,
            "custom": 100,
        }
        self.target_var.set(defaults.get(gt, 1000))

        # Показать или скрыть custom-параметры
        if gt == "custom":
            self.custom_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.custom_frame.pack_forget()

    def _parse_pairs(self, text: str, key_type=int, value_type=int) -> dict:
        """Парсит строку вида '3:50, 4:150' в словарь."""
        text = text.strip()
        if not text:
            return {}
        result = {}
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            if ":" not in part:
                raise ValueError(f"Ожидался формат N:бонус в фрагменте «{part}»")
            k, v = part.split(":", 1)
            result[key_type(k.strip())] = value_type(v.strip())
        return result

    def apply_rules(self):
        gt = self.game_type_var.get()
        target = self.target_var.get()
        try:
            if gt == "five_thousand":
                rules = FiveThousandRules(target_score=target)
            elif gt == "poker_dice":
                rules = PokerDiceRules(target_score=target)
            elif gt == "custom":
                bonuses = self._parse_pairs(self.bonuses_var.get())
                penalties = self._parse_pairs(self.penalties_var.get())
                config = CustomGameConfig(
                    num_dice=self.custom_num_dice_var.get(),
                    dice_type=self.custom_dice_type_var.get(),
                    target_score=target,
                    base_points_is_sum=self.base_sum_var.get(),
                    bonus_n_of_a_kind=bonuses,
                    penalty_values=penalties,
                )
                rules = CustomGameRules(config=config)
            else:
                raise ValueError(f"Неизвестный тип: {gt}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Невалидные правила: {e}")
            return

        if not messagebox.askyesno(
            "Подтверждение",
            "Создать новую игру с этими правилами? Текущая игра будет сброшена."
        ):
            return

        self.controller.start_new_game(rules)
        messagebox.showinfo("Готово", "Новая игра создана. Добавьте игроков на вкладке «Игроки».")
