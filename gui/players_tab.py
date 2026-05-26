"""
Вкладка «Игроки» — добавление, удаление и просмотр игроков.
"""
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser


class PlayersTab(ttk.Frame):
    """Вкладка управления игроками."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Верхняя панель — форма добавления
        top = ttk.LabelFrame(self, text="Добавить игрока", padding=10)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Имя:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(top, textvariable=self.name_var, width=24)
        self.name_entry.grid(row=0, column=1, padx=5)
        self.name_entry.bind("<Return>", lambda e: self.add_player())

        self.add_btn = ttk.Button(top, text="➕ Добавить", command=self.add_player)
        self.add_btn.grid(row=0, column=2, padx=5)

        ttk.Label(top, text="(можно от 2 до 8 игроков)").grid(
            row=0, column=3, padx=15, sticky="w"
        )

        # Таблица игроков
        list_frame = ttk.LabelFrame(self, text="Игроки", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(
            list_frame,
            columns=("name", "score", "rolls", "avg", "best"),
            show="headings",
            height=10,
        )
        self.tree.heading("name", text="Имя")
        self.tree.heading("score", text="Очки")
        self.tree.heading("rolls", text="Бросков")
        self.tree.heading("avg", text="Сред. кубик")
        self.tree.heading("best", text="Лучший бросок")
        self.tree.column("name", width=160)
        self.tree.column("score", width=80, anchor="e")
        self.tree.column("rolls", width=80, anchor="e")
        self.tree.column("avg", width=100, anchor="e")
        self.tree.column("best", width=120, anchor="e")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Кнопки
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            btns, text="🎨 Изменить цвет", command=self.change_color
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btns, text="🗑 Удалить", command=self.remove_player
        ).pack(side=tk.LEFT, padx=5)

    def add_player(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Введите имя игрока")
            return
        if len(name) > 30:
            messagebox.showwarning("Внимание", "Имя слишком длинное (макс. 30 символов)")
            return
        game = self.controller.game
        if game is None:
            messagebox.showinfo("Информация", "Сначала создайте игру (вкладка «Игра»)")
            return
        if len(game.players) >= 8:
            messagebox.showwarning("Внимание", "Максимум 8 игроков")
            return
        try:
            game.add_player(name)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
        self.name_var.set("")
        self.update_from_game()
        self.controller.update_all_tabs()

    def remove_player(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите игрока для удаления")
            return
        name = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Подтверждение", f"Удалить игрока «{name}»?"):
            return
        game = self.controller.game
        if game is None:
            return
        game.remove_player(str(name))
        self.update_from_game()
        self.controller.update_all_tabs()

    def change_color(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите игрока")
            return
        name = self.tree.item(sel[0])["values"][0]
        game = self.controller.game
        if game is None:
            return
        player = next((p for p in game.players if p.name == str(name)), None)
        if player is None:
            return
        color = colorchooser.askcolor(
            initialcolor=player.color, title="Цвет игрока"
        )
        if color and color[1]:
            player.color = color[1]
            self.update_from_game()
            self.controller.update_all_tabs()

    def update_from_game(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        game = self.controller.game
        if game is None:
            return
        for p in game.players:
            tag = f"player_{p.name}"
            self.tree.insert(
                "", "end",
                values=(
                    p.name,
                    p.score,
                    p.total_rolls,
                    f"{p.average_roll:.2f}",
                    p.highest_total,
                ),
                tags=(tag,),
            )
            try:
                self.tree.tag_configure(tag, foreground=p.color)
            except tk.TclError:
                pass
