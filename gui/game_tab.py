"""
Вкладка «Игра» — основное игровое поле.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from game_logic.dice import DICE_TYPES
from gui.dice_animation import DiceAnimation


class GameTab(ttk.Frame):
    """Вкладка с игровым процессом."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller  # ссылка на MainWindow
        self._build_ui()

    def _build_ui(self):
        # Верхняя панель: информация о текущей игре и игроке
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        self.game_label = ttk.Label(top, text="Игра не запущена", font=("Helvetica", 14, "bold"))
        self.game_label.pack(side=tk.LEFT)

        self.round_label = ttk.Label(top, text="", font=("Helvetica", 11))
        self.round_label.pack(side=tk.RIGHT)

        # Центр: левая колонка — кубики и кнопки, правая — таблица лидеров
        center = ttk.Frame(self)
        center.pack(fill=tk.BOTH, expand=True, padx=10)

        # ----- Левая колонка -----
        left = ttk.Frame(center)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Подпись текущего игрока
        self.current_player_label = ttk.Label(
            left, text="Ход: —", font=("Helvetica", 13, "bold")
        )
        self.current_player_label.pack(anchor="w", pady=(0, 8))

        # Анимация кубиков
        self.dice_animation = DiceAnimation(left, dice_size=72)
        self.dice_animation.pack(anchor="w", pady=8)

        # Параметры броска
        params = ttk.LabelFrame(left, text="Параметры броска", padding=10)
        params.pack(fill=tk.X, pady=10)

        ttk.Label(params, text="Тип:").grid(row=0, column=0, sticky="w")
        self.dice_type_var = tk.StringVar(value="D6")
        self.dice_type_combo = ttk.Combobox(
            params, textvariable=self.dice_type_var,
            values=list(DICE_TYPES.keys()), state="readonly", width=6
        )
        self.dice_type_combo.grid(row=0, column=1, padx=5)

        ttk.Label(params, text="Кол-во:").grid(row=0, column=2, sticky="w", padx=(15, 0))
        self.num_dice_var = tk.IntVar(value=5)
        self.num_dice_spin = ttk.Spinbox(
            params, from_=1, to=20, textvariable=self.num_dice_var, width=5
        )
        self.num_dice_spin.grid(row=0, column=3, padx=5)

        ttk.Label(params, text="Модификатор:").grid(row=0, column=4, sticky="w", padx=(15, 0))
        self.modifier_var = tk.IntVar(value=0)
        self.modifier_spin = ttk.Spinbox(
            params, from_=-50, to=50, textvariable=self.modifier_var, width=5
        )
        self.modifier_spin.grid(row=0, column=5, padx=5)

        self.lock_params_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            params, text="По правилам игры (фиксированные параметры)",
            variable=self.lock_params_var, command=self._toggle_lock
        ).grid(row=1, column=0, columnspan=6, sticky="w", pady=(8, 0))

        # Кнопки управления
        buttons = ttk.Frame(left)
        buttons.pack(fill=tk.X, pady=10)

        self.roll_btn = ttk.Button(
            buttons, text="🎲 Бросить (Space)", command=self.controller.on_roll
        )
        self.roll_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.next_btn = ttk.Button(
            buttons, text="➡ Следующий игрок (Enter)", command=self.controller.on_next_player
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)

        self.new_btn = ttk.Button(
            buttons, text="🔄 Новая игра", command=self.controller.on_new_game
        )
        self.new_btn.pack(side=tk.LEFT, padx=5)

        # Результат последнего броска
        result_frame = ttk.LabelFrame(left, text="Результат броска", padding=10)
        result_frame.pack(fill=tk.X, pady=10)
        self.result_label = ttk.Label(
            result_frame, text="—", font=("Helvetica", 12), wraplength=400, justify="left"
        )
        self.result_label.pack(anchor="w")

        # ----- Правая колонка: таблица лидеров -----
        right = ttk.LabelFrame(center, text="Таблица лидеров", padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        self.leaderboard = ttk.Treeview(
            right,
            columns=("place", "name", "score", "rolls"),
            show="headings",
            height=12,
        )
        self.leaderboard.heading("place", text="#")
        self.leaderboard.heading("name", text="Игрок")
        self.leaderboard.heading("score", text="Очки")
        self.leaderboard.heading("rolls", text="Бросков")
        self.leaderboard.column("place", width=30, anchor="center")
        self.leaderboard.column("name", width=140)
        self.leaderboard.column("score", width=70, anchor="e")
        self.leaderboard.column("rolls", width=70, anchor="e")
        self.leaderboard.pack(fill=tk.BOTH, expand=True)

        self._toggle_lock()

    def _toggle_lock(self):
        """Включить/отключить ручные параметры броска."""
        state = "disabled" if self.lock_params_var.get() else "readonly"
        self.dice_type_combo.configure(state=state)
        spin_state = "disabled" if self.lock_params_var.get() else "normal"
        self.num_dice_spin.configure(state=spin_state)
        # Модификатор всегда можно

    # ------- Обновление UI на основе состояния -------

    def update_from_game(self):
        """Обновить вкладку из состояния игры контроллера."""
        game = self.controller.game
        if game is None:
            self.game_label.configure(text="Игра не запущена")
            self.round_label.configure(text="")
            self.current_player_label.configure(text="Ход: —")
            self._clear_leaderboard()
            return

        self.game_label.configure(
            text=f"{game.rules.name} — цель: {game.rules.target_score}"
        )
        self.round_label.configure(text=f"Раунд: {game.round_number}")

        # текущий игрок
        cp = game.current_player
        if cp is None:
            self.current_player_label.configure(text="Ход: —")
        else:
            self.current_player_label.configure(
                text=f"Ход: {cp.name}",
                foreground=cp.color,
            )

        # Если правила фиксированные — обновим параметры
        if self.lock_params_var.get():
            self.dice_type_var.set(game.rules.dice_type)
            self.num_dice_var.set(game.rules.num_dice)

        # таблица лидеров
        self._update_leaderboard()

        # если есть победитель — заблокировать «бросить»
        if game.winner is not None:
            self.roll_btn.configure(state="disabled")
        else:
            self.roll_btn.configure(state="normal")

    def show_roll_result(self, roll, turn_result):
        """Показать на экране результат последнего броска."""
        self.dice_animation.animate_roll(
            final_values=roll.values,
            dice_type=roll.dice_type,
        )
        text = (
            f"{roll}  →  {turn_result.combination}\n"
            f"Очков за ход: {turn_result.points:+d}"
        )
        self.result_label.configure(text=text)
        self._update_leaderboard()

    def get_roll_params(self):
        """Получить параметры броска из формы."""
        return (
            self.num_dice_var.get(),
            self.dice_type_var.get(),
            self.modifier_var.get(),
        )

    def _update_leaderboard(self):
        self._clear_leaderboard()
        game = self.controller.game
        if game is None:
            return
        for i, p in enumerate(game.get_leaderboard(), start=1):
            tag = f"player_{i}"
            self.leaderboard.insert(
                "", "end",
                values=(i, p.name, p.score, p.total_rolls),
                tags=(tag,),
            )
            try:
                self.leaderboard.tag_configure(tag, foreground=p.color)
            except tk.TclError:
                pass

    def _clear_leaderboard(self):
        for item in self.leaderboard.get_children():
            self.leaderboard.delete(item)
