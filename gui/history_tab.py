"""
Вкладка «История» — журнал всех событий игры.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from data.save_load import export_to_csv


class HistoryTab(ttk.Frame):
    """Вкладка истории."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(top, text="Журнал событий игры", font=("Helvetica", 12, "bold")).pack(
            side=tk.LEFT
        )
        ttk.Button(top, text="🔄 Обновить", command=self.update_from_game).pack(side=tk.RIGHT)
        ttk.Button(top, text="📤 Экспорт в CSV", command=self.export_csv).pack(
            side=tk.RIGHT, padx=5
        )

        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text = tk.Text(text_frame, wrap="word", font=("Consolas", 10), height=20)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=scrollbar.set, state="disabled")

    def update_from_game(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        game = self.controller.game
        if game is None:
            self.text.insert(tk.END, "Игра не запущена.\n")
        else:
            for entry in game.history:
                self.text.insert(tk.END, entry + "\n")
        self.text.see(tk.END)
        self.text.configure(state="disabled")

    def export_csv(self):
        game = self.controller.game
        if game is None or not game.dice_roller.history:
            messagebox.showinfo("Информация", "Нет данных для экспорта")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            title="Экспорт истории бросков"
        )
        if not path:
            return
        try:
            export_to_csv(game, path)
            messagebox.showinfo("Готово", f"Экспортировано в:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")
