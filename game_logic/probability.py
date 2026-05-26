"""
Вероятностные расчёты для бросков кубиков.
Включает: распределение суммы N кубиков, вероятности порогов,
сравнение теоретических и фактических данных.
"""
from collections import Counter
from functools import lru_cache
from typing import Dict, List, Tuple

import numpy as np

from game_logic.dice import DICE_TYPES


@lru_cache(maxsize=64)
def sum_distribution(num_dice: int, sides: int) -> Dict[int, float]:
    """
    Точное распределение вероятностей суммы для num_dice кубиков с `sides` гранями.

    Возвращает словарь {сумма: вероятность}, сумма от num_dice до num_dice*sides.

    Использует динамическое программирование (свёртку), а не перебор всех исходов,
    что позволяет работать даже для 20D20.
    """
    if num_dice <= 0 or sides <= 0:
        raise ValueError("num_dice и sides должны быть положительными")

    # distribution[s] = число исходов с суммой s
    # для одного кубика: каждое число от 1 до sides имеет 1 исход
    distribution = np.zeros(num_dice * sides + 1, dtype=np.float64)
    # начальное распределение для одного кубика
    one_die = np.zeros(sides + 1, dtype=np.float64)
    for face in range(1, sides + 1):
        one_die[face] = 1.0

    # начальная свёртка
    current = one_die.copy()
    for _ in range(num_dice - 1):
        current = np.convolve(current, one_die)

    total_outcomes = sides ** num_dice
    result = {}
    for s, count in enumerate(current):
        if count > 0:
            result[s] = count / total_outcomes
    return result


def expected_sum(num_dice: int, dice_type: str, modifier: int = 0) -> float:
    """Математическое ожидание суммы N кубиков с модификатором."""
    sides = DICE_TYPES[dice_type]
    return num_dice * (sides + 1) / 2 + modifier


def variance_sum(num_dice: int, dice_type: str) -> float:
    """Дисперсия суммы N независимых кубиков."""
    sides = DICE_TYPES[dice_type]
    return num_dice * (sides ** 2 - 1) / 12


def std_sum(num_dice: int, dice_type: str) -> float:
    """Стандартное отклонение суммы."""
    return float(np.sqrt(variance_sum(num_dice, dice_type)))


def probability_at_least(
    threshold: int,
    num_dice: int,
    dice_type: str,
    modifier: int = 0,
) -> float:
    """Вероятность того, что сумма >= threshold."""
    sides = DICE_TYPES[dice_type]
    dist = sum_distribution(num_dice, sides)
    return sum(p for s, p in dist.items() if s + modifier >= threshold)


def probability_at_most(
    threshold: int,
    num_dice: int,
    dice_type: str,
    modifier: int = 0,
) -> float:
    """Вероятность того, что сумма <= threshold."""
    sides = DICE_TYPES[dice_type]
    dist = sum_distribution(num_dice, sides)
    return sum(p for s, p in dist.items() if s + modifier <= threshold)


def probability_equals(
    target: int,
    num_dice: int,
    dice_type: str,
    modifier: int = 0,
) -> float:
    """Вероятность того, что сумма равна target."""
    sides = DICE_TYPES[dice_type]
    dist = sum_distribution(num_dice, sides)
    return dist.get(target - modifier, 0.0)


def probability_in_range(
    low: int,
    high: int,
    num_dice: int,
    dice_type: str,
    modifier: int = 0,
) -> float:
    """Вероятность того, что low <= сумма <= high."""
    sides = DICE_TYPES[dice_type]
    dist = sum_distribution(num_dice, sides)
    return sum(p for s, p in dist.items() if low <= s + modifier <= high)


def theoretical_frequencies(
    num_dice: int,
    dice_type: str,
    num_rolls: int,
) -> Dict[int, float]:
    """Ожидаемое количество появлений каждой суммы при заданном числе бросков."""
    sides = DICE_TYPES[dice_type]
    dist = sum_distribution(num_dice, sides)
    return {s: p * num_rolls for s, p in dist.items()}


def empirical_distribution(values: List[int]) -> Dict[int, float]:
    """Эмпирическое распределение наблюдаемых значений."""
    if not values:
        return {}
    counter = Counter(values)
    total = len(values)
    return {v: c / total for v, c in counter.items()}


def chi_square_test(
    observed_values: List[int],
    num_dice: int,
    dice_type: str,
) -> Tuple[float, int]:
    """
    Простейший хи-квадрат критерий на соответствие наблюдаемых сумм
    теоретическому распределению.

    Возвращает (значение хи-квадрата, число степеней свободы).
    Чем меньше значение, тем ближе наблюдения к теории.
    """
    if not observed_values:
        return 0.0, 0
    sides = DICE_TYPES[dice_type]
    theory = sum_distribution(num_dice, sides)
    n = len(observed_values)
    observed = Counter(observed_values)

    chi2 = 0.0
    df = 0
    for s, p in theory.items():
        expected = p * n
        if expected < 5:
            # для совсем редких сумм пропускаем (стандартное правило)
            continue
        obs = observed.get(s, 0)
        chi2 += (obs - expected) ** 2 / expected
        df += 1
    df = max(df - 1, 1)  # одна степень свободы съедается нормировкой
    return chi2, df
