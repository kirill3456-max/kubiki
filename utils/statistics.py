"""
Статистические утилиты: средние, дисперсия, гистограммы и т.п.
"""
from collections import Counter
from typing import Dict, List, Tuple

import numpy as np


def basic_stats(values: List[int]) -> Dict[str, float]:
    """Базовая статистика: count, mean, std, min, max, median."""
    if not values:
        return {
            "count": 0, "mean": 0.0, "std": 0.0,
            "min": 0, "max": 0, "median": 0.0
        }
    arr = np.array(values)
    return {
        "count": int(arr.size),
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=0)),
        "min": int(arr.min()),
        "max": int(arr.max()),
        "median": float(np.median(arr)),
    }


def histogram(values: List[int], min_val: int = None, max_val: int = None) -> Dict[int, int]:
    """Гистограмма (частоты появления значений)."""
    if not values:
        return {}
    counter = Counter(values)
    if min_val is None:
        min_val = min(counter)
    if max_val is None:
        max_val = max(counter)
    return {v: counter.get(v, 0) for v in range(min_val, max_val + 1)}


def deviation_from_expected(
    observed: List[int],
    expected_freqs: Dict[int, float],
) -> Dict[int, float]:
    """
    Возвращает разность (observed_count - expected_count) для каждого значения.
    Полезно для отображения «насколько повезло/не повезло».
    """
    obs_counter = Counter(observed)
    result = {}
    for value, expected_count in expected_freqs.items():
        result[value] = obs_counter.get(value, 0) - expected_count
    # Также добавим значения, которые наблюдались, но не входят в ожидаемые
    for value, count in obs_counter.items():
        if value not in result:
            result[value] = count
    return result


def win_rate(player_wins: int, total_games: int) -> float:
    """Доля побед в процентах."""
    if total_games == 0:
        return 0.0
    return 100.0 * player_wins / total_games
