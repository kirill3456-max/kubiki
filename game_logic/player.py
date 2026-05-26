"""
Модуль игрока. Хранит данные об игроке: имя, очки, историю ходов.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any

from game_logic.dice import RollResult


# Палитра цветов для аватаров игроков (до 8 игроков)
PLAYER_COLORS = [
    "#E74C3C",  # красный
    "#3498DB",  # синий
    "#2ECC71",  # зелёный
    "#F39C12",  # оранжевый
    "#9B59B6",  # фиолетовый
    "#1ABC9C",  # бирюзовый
    "#E67E22",  # тёмно-оранжевый
    "#34495E",  # тёмно-синий
]


@dataclass
class Player:
    """Игрок в настольной игре."""
    name: str
    score: int = 0
    color: str = "#3498DB"
    rolls: List[RollResult] = field(default_factory=list)
    turn_log: List[str] = field(default_factory=list)  # текстовая история ходов

    def add_score(self, points: int) -> None:
        """Добавить (или вычесть, если отрицательное) очков."""
        self.score += points

    def add_roll(self, roll: RollResult) -> None:
        """Зарегистрировать бросок этого игрока."""
        self.rolls.append(roll)

    def add_turn_log(self, message: str) -> None:
        """Добавить запись в журнал ходов игрока."""
        self.turn_log.append(message)

    def reset(self) -> None:
        """Сбросить состояние игрока (новый раунд / новая игра)."""
        self.score = 0
        self.rolls.clear()
        self.turn_log.clear()

    # ------------- Статистика -------------

    @property
    def total_rolls(self) -> int:
        """Общее число выполненных бросков (групп бросков)."""
        return len(self.rolls)

    @property
    def total_dice_thrown(self) -> int:
        """Общее число брошенных кубиков (одиночных)."""
        return sum(r.num_dice for r in self.rolls)

    @property
    def average_roll(self) -> float:
        """Средний результат одного кубика игрока."""
        all_vals = [v for r in self.rolls for v in r.values]
        if not all_vals:
            return 0.0
        return sum(all_vals) / len(all_vals)

    @property
    def average_total(self) -> float:
        """Среднее по сумме броска (включая модификатор)."""
        if not self.rolls:
            return 0.0
        return sum(r.total for r in self.rolls) / len(self.rolls)

    @property
    def highest_total(self) -> int:
        """Самый удачный бросок."""
        return max((r.total for r in self.rolls), default=0)

    @property
    def lowest_total(self) -> int:
        """Самый неудачный бросок."""
        return min((r.total for r in self.rolls), default=0)

    # ------------- Сериализация -------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "color": self.color,
            "rolls": [r.to_dict() for r in self.rolls],
            "turn_log": list(self.turn_log),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        return cls(
            name=data["name"],
            score=data.get("score", 0),
            color=data.get("color", "#3498DB"),
            rolls=[RollResult.from_dict(r) for r in data.get("rolls", [])],
            turn_log=list(data.get("turn_log", [])),
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.score} очков)"
