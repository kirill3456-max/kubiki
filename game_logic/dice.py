"""
Модуль кубиков (dice).
Содержит классы для всех типов кубиков и операций бросков.
"""
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


# Поддерживаемые типы кубиков и количество их граней
DICE_TYPES = {
    "D4": 4,
    "D6": 6,
    "D8": 8,
    "D10": 10,
    "D12": 12,
    "D20": 20,
    "D100": 100,
}


@dataclass
class RollResult:
    """Результат одного броска (возможно, нескольких кубиков)."""
    dice_type: str               # Например, "D6"
    num_dice: int                # Сколько кубиков бросалось
    values: List[int]            # Выпавшие значения каждого кубика
    modifier: int = 0            # Модификатор +/-
    player_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> int:
        """Сумма всех кубиков с учётом модификатора."""
        return sum(self.values) + self.modifier

    def to_dict(self) -> dict:
        """Сериализация в словарь для JSON."""
        return {
            "dice_type": self.dice_type,
            "num_dice": self.num_dice,
            "values": list(self.values),
            "modifier": self.modifier,
            "total": self.total,
            "player_name": self.player_name,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RollResult":
        """Восстановление из словаря."""
        return cls(
            dice_type=data["dice_type"],
            num_dice=data["num_dice"],
            values=list(data["values"]),
            modifier=data.get("modifier", 0),
            player_name=data.get("player_name"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )

    def __str__(self) -> str:
        mod_str = ""
        if self.modifier > 0:
            mod_str = f" + {self.modifier}"
        elif self.modifier < 0:
            mod_str = f" - {abs(self.modifier)}"
        return (
            f"{self.num_dice}{self.dice_type}: "
            f"{self.values}{mod_str} = {self.total}"
        )


class Dice:
    """
    Класс одного кубика заданного типа.
    Поддерживает броски и расчёт теоретических вероятностей.
    """

    def __init__(self, dice_type: str = "D6"):
        if dice_type not in DICE_TYPES:
            raise ValueError(
                f"Неподдерживаемый тип кубика: {dice_type}. "
                f"Допустимы: {list(DICE_TYPES.keys())}"
            )
        self.dice_type = dice_type
        self.sides = DICE_TYPES[dice_type]

    def roll(self) -> int:
        """Бросить один кубик и вернуть выпавшее число."""
        return random.randint(1, self.sides)

    @property
    def expected_value(self) -> float:
        """Математическое ожидание одного кубика: (n+1)/2."""
        return (self.sides + 1) / 2

    @property
    def variance(self) -> float:
        """Дисперсия одного кубика: (n^2 - 1) / 12."""
        return (self.sides ** 2 - 1) / 12

    def __repr__(self) -> str:
        return f"Dice({self.dice_type})"


class DiceRoller:
    """
    Высокоуровневый интерфейс для бросков нескольких кубиков.
    Хранит историю всех бросков сессии.
    """

    def __init__(self):
        self.history: List[RollResult] = []

    def roll(
        self,
        num_dice: int = 1,
        dice_type: str = "D6",
        modifier: int = 0,
        player_name: Optional[str] = None,
    ) -> RollResult:
        """
        Бросить `num_dice` кубиков типа `dice_type` с модификатором.

        :param num_dice: количество кубиков (1..100)
        :param dice_type: тип кубика, например "D6"
        :param modifier: модификатор, прибавляемый к сумме
        :param player_name: имя игрока, выполняющего бросок
        :return: RollResult
        """
        if not 1 <= num_dice <= 100:
            raise ValueError("Количество кубиков должно быть от 1 до 100")
        dice = Dice(dice_type)
        values = [dice.roll() for _ in range(num_dice)]
        result = RollResult(
            dice_type=dice_type,
            num_dice=num_dice,
            values=values,
            modifier=modifier,
            player_name=player_name,
        )
        self.history.append(result)
        return result

    def clear_history(self) -> None:
        """Очистить историю бросков."""
        self.history.clear()

    def get_player_history(self, player_name: str) -> List[RollResult]:
        """Получить историю бросков конкретного игрока."""
        return [r for r in self.history if r.player_name == player_name]

    def all_values(self) -> List[int]:
        """Все выпавшие числа за сессию (плоский список)."""
        return [v for r in self.history for v in r.values]
