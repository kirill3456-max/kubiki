"""
Главное окно приложения с вкладками.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from data.save_load import save_game, load_game, list_saved_games, SAVES_DIR
from game_logic.game_rules import Game
from gui.game_tab import GameTab
from gui.players_tab import PlayersTab
from gui.stats_tab import StatsTab
from gui.rules_tab import RulesTab
from gui.history_tab import HistoryTab
from presets import FiveThousandRules
from utils.logger import get_logger


class MainWindow:
    """
    Главное окно: контроллер всего приложения.
    Хранит ссылку на текущую Game и координирует обновления вкладок.
    """

    AUTOSAVE_EVERY = 5  # автосохранение каждые N бросков

    def __init__(self):
        self.logger = get_logger()
        self.root = tk.Tk()
        self.root.title("Симулятор настольных игр — вероятностные модели")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)

        # Текущая игра (по умолчанию — Пятитысяч, без игроков)
        self.game: Game = Game(FiveThousandRules())
        self._rolls_since_autosave = 0

        self._setup_styles()
        self._build_menu()
        self._build_notebook()
        self._setup_hotkeys()

        # Тема (тёмная/светлая)
        self.dark_mode = False

        self.update_all_tabs()

    # ----------- Сборка -----------

    def _setup_styles(self):
        self.style = ttk.Style(self.root)
        # Попытаемся использовать «clam» — он стабильно поддерживает кастомные цвета
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новая игра…", command=self.on_new_game, accelerator="Ctrl+N")
        file_menu.add_command(label="Сохранить…", command=self.on_save, accelerator="Ctrl+S")
        file_menu.add_command(label="Загрузить…", command=self.on_load, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        # Вид
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Переключить тему", command=self.toggle_theme)
        menubar.add_cascade(label="Вид", menu=view_menu)

        # Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Горячие клавиши", command=self._show_hotkeys)
        help_menu.add_command(label="О программе", command=self._show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.configure(menu=menubar)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.game_tab = GameTab(self.notebook, self)
        self.players_tab = PlayersTab(self.notebook, self)
        self.stats_tab = StatsTab(self.notebook, self)
        self.rules_tab = RulesTab(self.notebook, self)
        self.history_tab = HistoryTab(self.notebook, self)

        self.notebook.add(self.game_tab, text="🎲 Игра")
        self.notebook.add(self.players_tab, text="👥 Игроки")
        self.notebook.add(self.stats_tab, text="📊 Статистика")
        self.notebook.add(self.rules_tab, text="⚙ Правила")
        self.notebook.add(self.history_tab, text="📜 История")

        # Строка статуса
        self.status_var = tk.StringVar(value="Готов. Добавьте игроков и бросайте кубики.")
        status = ttk.Label(
            self.root, textvariable=self.status_var, anchor="w",
            padding=(10, 4), relief=tk.SUNKEN
        )
        status.pack(fill=tk.X, side=tk.BOTTOM)

    def _setup_hotkeys(self):
        self.root.bind("<space>", lambda e: self.on_roll())
        self.root.bind("<Return>", lambda e: self.on_next_player())
        self.root.bind("<Control-n>", lambda e: self.on_new_game())
        self.root.bind("<Control-N>", lambda e: self.on_new_game())
        self.root.bind("<Control-s>", lambda e: self.on_save())
        self.root.bind("<Control-S>", lambda e: self.on_save())
        self.root.bind("<Control-o>", lambda e: self.on_load())
        self.root.bind("<Control-O>", lambda e: self.on_load())

    # ----------- Действия -----------

    def on_roll(self):
        if self.game is None or not self.game.players:
            self.status_var.set("Нет игроков — добавьте хотя бы одного на вкладке «Игроки».")
            return
        if self.game.winner is not None:
            self.status_var.set("Игра окончена. Начните новую.")
            return

        # Параметры броска
        if self.game_tab.lock_params_var.get():
            num_dice, dice_type, modifier = (
                self.game.rules.num_dice,
                self.game.rules.dice_type,
                self.game_tab.modifier_var.get(),
            )
        else:
            num_dice, dice_type, modifier = self.game_tab.get_roll_params()

        try:
            turn = self.game.roll_dice(
                num_dice=num_dice,
                dice_type=dice_type,
                modifier=modifier,
            )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return

        self.game_tab.show_roll_result(turn.roll, turn)
        self.status_var.set(
            f"{turn.roll.player_name}: {turn.combination} ({turn.points:+d} очк.)"
        )
        self.update_all_tabs(skip_game=True)  # game_tab уже обновлён через show_roll_result

        # Победа?
        if self.game.winner is not None:
            messagebox.showinfo(
                "🏆 Победа!",
                f"Победитель: {self.game.winner.name}\n"
                f"Очки: {self.game.winner.score}"
            )

        # Автосохранение
        self._rolls_since_autosave += 1
        if self._rolls_since_autosave >= self.AUTOSAVE_EVERY:
            self._autosave()
            self._rolls_since_autosave = 0

    def on_next_player(self):
        if self.game is None or not self.game.players:
            return
        nxt = self.game.next_player()
        if nxt is not None:
            self.status_var.set(f"Ход переходит к: {nxt.name}")
        self.update_all_tabs()

    def on_new_game(self):
        """Сбросить текущую игру (правила остаются)."""
        if self.game is None:
            self.game = Game(FiveThousandRules())
            self.update_all_tabs()
            return
        if not messagebox.askyesno("Подтверждение", "Начать новую игру? Прогресс будет сброшен."):
            return
        rules = self.game.rules
        # Сохраняем имена и цвета игроков
        old_players = [(p.name, p.color) for p in self.game.players]
        # Создаём новую с теми же правилами
        rules_class = type(rules)
        # пытаемся пересоздать с теми же параметрами
        try:
            new_rules = rules_class()  # default args
            # переносим target_score
            new_rules.target_score = rules.target_score
            new_rules.num_dice = rules.num_dice
            new_rules.dice_type = rules.dice_type
        except Exception:
            new_rules = rules
        self.game = Game(new_rules)
        for name, color in old_players:
            try:
                p = self.game.add_player(name)
                p.color = color
            except Exception:
                pass
        self._rolls_since_autosave = 0
        self.status_var.set("Новая игра начата.")
        self.update_all_tabs()

    def start_new_game(self, rules):
        """Создать совсем новую игру с указанными правилами (используется из RulesTab)."""
        self.game = Game(rules)
        self._rolls_since_autosave = 0
        self.status_var.set(f"Создана игра: {rules.name}")
        self.update_all_tabs()

    def on_save(self):
        if self.game is None or not self.game.players:
            messagebox.showinfo("Информация", "Нечего сохранять")
            return
        path = filedialog.asksaveasfilename(
            initialdir=SAVES_DIR,
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
            title="Сохранить игру",
        )
        if not path:
            return
        try:
            actual = save_game(self.game, path)
            self.status_var.set(f"Сохранено: {os.path.basename(actual)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def on_load(self):
        path = filedialog.askopenfilename(
            initialdir=SAVES_DIR,
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
            title="Загрузить игру",
        )
        if not path:
            return
        try:
            self.game = load_game(path)
            self._rolls_since_autosave = 0
            self.status_var.set(f"Загружено: {os.path.basename(path)}")
            self.update_all_tabs()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
            self.logger.exception("load failed")

    def _autosave(self):
        try:
            path = save_game(self.game, "autosave.json")
            self.logger.info(f"Автосохранение: {path}")
        except Exception as e:
            self.logger.warning(f"Автосохранение не удалось: {e}")

    # ----------- Темы -----------

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            bg = "#2C3E50"
            fg = "#ECF0F1"
        else:
            bg = "#FFFFFF"
            fg = "#000000"
        self.root.configure(bg=bg)
        try:
            self.style.configure(".", background=bg, foreground=fg, fieldbackground=bg)
            self.style.configure("TLabel", background=bg, foreground=fg)
            self.style.configure("TFrame", background=bg)
            self.style.configure("TLabelframe", background=bg, foreground=fg)
            self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
            self.style.configure("TNotebook", background=bg)
            self.style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg)
        except tk.TclError:
            pass
        try:
            self.game_tab.dice_animation.set_dark_mode(self.dark_mode)
        except Exception:
            pass

    # ----------- Справка -----------

    def _show_hotkeys(self):
        messagebox.showinfo(
            "Горячие клавиши",
            "Space — бросить кубики\n"
            "Enter — следующий игрок\n"
            "Ctrl+N — новая игра\n"
            "Ctrl+S — сохранить\n"
            "Ctrl+O — загрузить",
        )

    def _show_about(self):
        messagebox.showinfo(
            "О программе",
            "Симулятор настольных игр\n"
            "с вероятностными моделями случайных величин.\n\n"
            "Поддерживает кубики D4..D100, несколько типов игр, "
            "статистику, графики, экспорт в CSV.",
        )

    # ----------- Обновление -----------

    def update_all_tabs(self, skip_game: bool = False):
        """Обновить все вкладки из текущего состояния."""
        if not skip_game:
            self.game_tab.update_from_game()
        self.players_tab.update_from_game()
        self.stats_tab.update_from_game()
        self.history_tab.update_from_game()

    def run(self):
        self.root.mainloop()
