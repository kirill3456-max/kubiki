"""
Настраиваемая игра.

Игрок (или GUI) задаёт:
- количество кубиков и их тип
- целевые очки
- штрафы за конкретные значения (например, выпала «1» — штраф)
- бонусы за комбинации (количество одинаковых, диапазон суммы и т.п.)

По умолчанию: 2 D6, цель 100, без бонусов и штрафов. Очки = сумма броска.
"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from game_logic.dice import RollResult
from game_logic.game_rules import GameRules, TurnResult


@dataclass
class CustomGameConfig:
    """
    Конфигурация настраиваемой игры.

    bonus_n_of_a_kind: словарь {N: бонус} — за N одинаковых кубиков добавить X очков.
        Пример: {3: 50, 4: 150, 5: 300}.
    penalty_values: {значение: штраф} — за каждый выпавший кубик с этим значением вычесть очков.
        Пример: {1: 10}  — каждая «1» отнимает 10 очков.
    sum_bonus: список (low, high, bonus) — если сумма попадает в диапазон, прибавить бонус.
    base_points_is_sum: если True, базовые очки = сумма броска. Иначе = 0.
    """
    num_dice: int = 2
    dice_type: str = "D6"
    target_score: int = 100
    base_points_is_sum: bool = True
    bonus_n_of_a_kind: Dict[int, int] = field(default_factory=dict)
    penalty_values: Dict[int, int] = field(default_factory=dict)
    sum_bonus: List[Tuple[int, int, int]] = field(default_factory=list)


class CustomGameRules(GameRules):
    name = "Настраиваемая игра"
    description = (
        "Задайте свои кубики, цель и бонусы/штрафы — и играйте по своим правилам."
    )

    def __init__(self, config: CustomGameConfig = None):
        self.config = config or CustomGameConfig()
        self.num_dice = self.config.num_dice
        self.dice_type = self.config.dice_type
        self.target_score = self.config.target_score

    def calculate_points(self, roll: RollResult) -> TurnResult:
        cfg = self.config
        values = roll.values
        counter = Counter(values)

        # базовые очки
        points = roll.total if cfg.base_points_is_sum else 0
        combos = []

        # N одинаковых
        if cfg.bonus_n_of_a_kind:
            max_same = max(counter.values()) if counter else 0
            # Применяем максимально подходящий бонус (тройка, каре и т. д.)
            for n in sorted(cfg.bonus_n_of_a_kind.keys(), reverse=True):
                if max_same >= n:
                    bonus = cfg.bonus_n_of_a_kind[n]
                    points += bonus
                    combos.append(f"{n} одинаковых +{bonus}")
                    break

        # штрафы за конкретные значения
        for face, penalty in cfg.penalty_values.items():
            num_of_face = counter.get(face, 0)
            if num_of_face > 0:
                total_pen = num_of_face * penalty
                points -= total_pen
                combos.append(f"{num_of_face}×«{face}» -{total_pen}")

        # бонус за попадание суммы в диапазон
        s = roll.total
        for low, high, bonus in cfg.sum_bonus:
            if low <= s <= high:
                points += bonus
                combos.append(f"сумма {low}-{high} +{bonus}")

        combination = ", ".join(combos) if combos else "обычный бросок"
        return TurnResult(roll=roll, points=points, combination=combination)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["config"] = {
            "num_dice": self.config.num_dice,
            "dice_type": self.config.dice_type,
            "target_score": self.config.target_score,
            "base_points_is_sum": self.config.base_points_is_sum,
            "bonus_n_of_a_kind": dict(self.config.bonus_n_of_a_kind),
            "penalty_values": dict(self.config.penalty_values),
            "sum_bonus": list(self.config.sum_bonus),
        }
        return data
