"""
Игра «Пятитысяч» / «10000» (накопительная игра на 6 кубиках D6).

Подсчёт очков за бросок:
- Каждая 1 = 100 очков
- Каждая 5 = 50 очков
- Тройка одинаковых = число × 100 (тройка единиц = 1000)
- Четвёрка одинаковых = ×2 от тройки
- Пятёрка одинаковых = ×4 от тройки
- Стрит 1-2-3-4-5-6 = 1500 очков
- Три пары = 750 очков
- Если за бросок не выпало ни одного очкового набора — «провал», 0 очков

Игрок-победитель: первый, набравший 5000 (или target_score).
"""
from collections import Counter

from game_logic.dice import RollResult
from game_logic.game_rules import GameRules, TurnResult


class FiveThousandRules(GameRules):
    name = "Пятитысяч (10000)"
    description = (
        "Классическая накопительная игра на 6 кубиках D6. "
        "Набирайте комбинации, чтобы первым достичь целевого счёта."
    )
    num_dice = 6
    dice_type = "D6"
    target_score = 5000

    def __init__(self, target_score: int = 5000):
        self.target_score = target_score

    def calculate_points(self, roll: RollResult) -> TurnResult:
        if roll.dice_type != "D6":
            # для совместимости считаем «как D6», но в норме сюда придёт D6
            pass

        values = list(roll.values)
        counter = Counter(values)
        points = 0
        combos = []

        sorted_vals = sorted(values)

        # Стрит 1..6
        if len(values) >= 6 and sorted_vals[:6] == [1, 2, 3, 4, 5, 6]:
            return TurnResult(roll=roll, points=1500, combination="Стрит 1-2-3-4-5-6")

        # Три пары (только если ровно 6 кубиков и три значения по 2 раза)
        if len(values) == 6:
            pairs = [v for v, c in counter.items() if c == 2]
            if len(pairs) == 3:
                return TurnResult(roll=roll, points=750, combination="Три пары")

        # Считаем тройки/четвёрки/пятёрки/шестёрки и оставшиеся одиночки
        remaining = Counter(values)
        for face, count in list(counter.items()):
            if count >= 3:
                base = 1000 if face == 1 else face * 100
                multi_count = count - 3  # сколько лишних к тройке
                # Базовая тройка
                kind_pts = base
                # Множитель: 4 = x2, 5 = x4, 6 = x8 (каждый сверх — x2)
                multiplier = 2 ** multi_count
                pts = base * multiplier
                points += pts
                combos.append(
                    f"{count}×{face}={pts}"
                )
                # Эти кубики «съедены» комбинацией
                remaining[face] = 0

        # Одиночные единицы и пятёрки
        ones_left = remaining.get(1, 0)
        fives_left = remaining.get(5, 0)
        if ones_left:
            pts = ones_left * 100
            points += pts
            combos.append(f"{ones_left}×1={pts}")
        if fives_left:
            pts = fives_left * 50
            points += pts
            combos.append(f"{fives_left}×5={pts}")

        if points == 0:
            combination = "Провал"
        else:
            combination = ", ".join(combos)

        return TurnResult(roll=roll, points=points, combination=combination)
