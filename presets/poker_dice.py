"""
Покер на костях (5 кубиков D6).

Подсчёт за бросок (от старшего к младшему):
- Пять одинаковых   = 500
- Малый стрит 1-2-3-4-5 или 2-3-4-5-6 = 400
- Каре             = 300
- Фулл-хаус        = 250
- Тройка           = 150
- Две пары         = 100
- Пара             = 50
- Иначе            = сумма очков на кубиках

Победитель — первый, кто достигает target_score (по умолчанию 1000).
"""
from collections import Counter

from game_logic.dice import RollResult
from game_logic.game_rules import GameRules, TurnResult


class PokerDiceRules(GameRules):
    name = "Покер на костях"
    description = (
        "5 кубиков D6, комбинации как в покере. "
        "Зарабатывайте крупные комбинации, чтобы первым достичь целевого счёта."
    )
    num_dice = 5
    dice_type = "D6"
    target_score = 1000

    def __init__(self, target_score: int = 1000):
        self.target_score = target_score

    def calculate_points(self, roll: RollResult) -> TurnResult:
        values = sorted(roll.values)
        counter = Counter(values)
        counts = sorted(counter.values(), reverse=True)

        # Пять одинаковых
        if counts == [5]:
            return TurnResult(roll=roll, points=500, combination="Пять одинаковых")

        # Малый стрит на 5 кубиках
        if len(values) >= 5:
            unique_sorted = sorted(set(values))
            for start in (1, 2):
                target = list(range(start, start + 5))
                if all(v in unique_sorted for v in target):
                    return TurnResult(roll=roll, points=400, combination="Стрит")

        # Каре
        if counts and counts[0] == 4:
            return TurnResult(roll=roll, points=300, combination="Каре")

        # Фулл-хаус
        if counts[:2] == [3, 2]:
            return TurnResult(roll=roll, points=250, combination="Фулл-хаус")

        # Тройка
        if counts and counts[0] == 3:
            return TurnResult(roll=roll, points=150, combination="Тройка")

        # Две пары
        if counts.count(2) >= 2:
            return TurnResult(roll=roll, points=100, combination="Две пары")

        # Пара
        if counts and counts[0] == 2:
            return TurnResult(roll=roll, points=50, combination="Пара")

        # Иначе — сумма очков
        total = sum(values)
        return TurnResult(roll=roll, points=total, combination=f"Старшая (сумма {total})")
