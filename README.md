# Симулятор настольных игр с вероятностными моделями

Полноценное приложение на Python с графическим интерфейсом (Tkinter) для симуляции
настольных игр с кубиками. Поддерживает несколько готовых игр, настройку собственных
правил, статистику и анализ вероятностей.

## Возможности

- 🎲 **Кубики**: D4, D6, D8, D10, D12, D20, D100
- 🎯 **Игроки**: от 2 до 8 игроков, индивидуальные цвета и статистика
- 🎮 **Готовые игры**: Пятитысяч (10000), Покер на костях, настраиваемая игра
- 📊 **Статистика**: гистограммы, сравнение «теория vs практика», калькулятор
  вероятностей (P(сумма ≥ X), P(сумма ≤ X), P(сумма = X), P(в диапазоне))
- 🧪 **Тест случайности**: χ² на соответствие теоретическому распределению
- 💾 **Сохранение**: JSON (с автосохранением каждые 5 ходов), экспорт в CSV
- 🌓 **Темы**: светлая и тёмная
- ⌨ **Горячие клавиши**: Space, Enter, Ctrl+N/S/O

## Установка

Требуется Python 3.8+ и зависимости:

```bash
pip install numpy matplotlib
```

Tkinter входит в стандартную поставку Python на большинстве платформ. Если на Linux
его нет, поставьте отдельно:

```bash
sudo apt-get install python3-tk
```

## Запуск

```bash
cd game_simulator
python main.py
```

## Структура проекта

```
game_simulator/
├── main.py                 # Точка входа
├── gui/
│   ├── main_window.py      # Главное окно + контроллер
│   ├── game_tab.py         # Вкладка игры
│   ├── players_tab.py      # Вкладка игроков
│   ├── stats_tab.py        # Вкладка статистики
│   ├── rules_tab.py        # Вкладка правил
│   ├── history_tab.py      # Вкладка истории
│   └── dice_animation.py   # Анимация кубиков
├── game_logic/
│   ├── dice.py             # Кубики и броски
│   ├── player.py           # Класс игрока
│   ├── game_rules.py       # Базовый класс правил + Game-контроллер
│   └── probability.py      # Вероятностные расчёты
├── data/
│   ├── save_load.py        # Сохранение/загрузка
│   └── games/              # Сохранённые игры (JSON)
├── presets/
│   ├── five_thousand.py    # Игра «Пятитысяч»
│   ├── poker_dice.py       # Покер на костях
│   └── custom_game.py      # Настраиваемая игра
├── utils/
│   ├── statistics.py       # Статистические функции
│   └── logger.py           # Логирование
└── logs/                   # Файлы логов (создаётся автоматически)
```

## Пример программного использования

```python
from presets import FiveThousandRules
from game_logic.game_rules import Game

# Создать игру
rules = FiveThousandRules(target_score=5000)
game = Game(rules)

# Добавить игроков
game.add_player("Алиса")
game.add_player("Боб")

# Бросать кубики
while game.winner is None:
    turn = game.roll_dice()
    print(turn.roll, "→", turn.combination, turn.points)
    game.next_player()

print("Победитель:", game.winner.name)
```

## Добавление новой игры

1. Создайте подкласс `GameRules` в `presets/`, переопределите `calculate_points()`.
2. Зарегистрируйте класс в `presets/__init__.py` в словаре `PRESET_GAMES`.
3. Игра автоматически появится в списке на вкладке «Правила».

## Лицензия

MIT
