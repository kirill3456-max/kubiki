"""
Реестр пресетов игр. Чтобы добавить новую — импортируйте её и зарегистрируйте.
"""
from presets.five_thousand import FiveThousandRules
from presets.poker_dice import PokerDiceRules
from presets.custom_game import CustomGameRules, CustomGameConfig


PRESET_GAMES = {
    "five_thousand": FiveThousandRules,
    "poker_dice": PokerDiceRules,
    "custom": CustomGameRules,
}


def create_rules(game_type: str, **kwargs):
    """Фабрика создания правил по типу."""
    if game_type not in PRESET_GAMES:
        raise ValueError(
            f"Неизвестный тип игры: {game_type}. "
            f"Доступны: {list(PRESET_GAMES.keys())}"
        )
    return PRESET_GAMES[game_type](**kwargs)


__all__ = [
    "PRESET_GAMES",
    "create_rules",
    "FiveThousandRules",
    "PokerDiceRules",
    "CustomGameRules",
    "CustomGameConfig",
]
