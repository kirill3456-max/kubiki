"""
Сохранение и загрузка состояния игры в JSON, экспорт CSV.
"""
import csv
import json
import os
from datetime import datetime
from typing import List

from game_logic.dice import RollResult
from game_logic.game_rules import Game
from game_logic.player import Player
from presets import PRESET_GAMES, FiveThousandRules, PokerDiceRules, CustomGameRules
from presets.custom_game import CustomGameConfig


# Папка для сохранений (создаём при необходимости)
SAVES_DIR = os.path.join(os.path.dirname(__file__), "games")
os.makedirs(SAVES_DIR, exist_ok=True)


def save_game(game: Game, filename: str = None) -> str:
    """
    Сохраняет состояние игры в JSON-файл.
    Возвращает путь к файлу.
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_{timestamp}.json"
    if not filename.endswith(".json"):
        filename += ".json"

    path = os.path.join(SAVES_DIR, filename) if not os.path.isabs(filename) else filename

    data = game.to_dict()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _restore_rules(data: dict):
    """Восстановить объект правил из сохранённого словаря."""
    rules_class = data.get("rules_class", "")
    rules_data = data.get("rules", {})

    if rules_class == "FiveThousandRules":
        rules = FiveThousandRules(
            target_score=rules_data.get("target_score", 5000)
        )
    elif rules_class == "PokerDiceRules":
        rules = PokerDiceRules(
            target_score=rules_data.get("target_score", 1000)
        )
    elif rules_class == "CustomGameRules":
        config_data = rules_data.get("config", {})
        config = CustomGameConfig(
            num_dice=config_data.get("num_dice", 2),
            dice_type=config_data.get("dice_type", "D6"),
            target_score=config_data.get("target_score", 100),
            base_points_is_sum=config_data.get("base_points_is_sum", True),
            bonus_n_of_a_kind={
                int(k): v for k, v in config_data.get("bonus_n_of_a_kind", {}).items()
            },
            penalty_values={
                int(k): v for k, v in config_data.get("penalty_values", {}).items()
            },
            sum_bonus=[tuple(t) for t in config_data.get("sum_bonus", [])],
        )
        rules = CustomGameRules(config=config)
    else:
        # fallback — пятитысяч
        rules = FiveThousandRules()
    return rules


def load_game(path: str) -> Game:
    """Загрузить игру из JSON-файла."""
    if not os.path.isabs(path):
        path = os.path.join(SAVES_DIR, path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rules = _restore_rules(data)
    game = Game(rules)

    # Игроки
    for pdata in data.get("players", []):
        player = Player.from_dict(pdata)
        game.players.append(player)
        # Регистрируем броски игрока в общей истории кубиков
        for r in player.rolls:
            game.dice_roller.history.append(r)

    game.current_player_index = data.get("current_player_index", 0)
    if game.current_player_index >= len(game.players):
        game.current_player_index = 0
    game.round_number = data.get("round_number", 1)
    winner_name = data.get("winner_name")
    if winner_name:
        for p in game.players:
            if p.name == winner_name:
                game.winner = p
                break
    game.history = list(data.get("history", []))
    return game


def list_saved_games() -> List[str]:
    """Список сохранённых игр (имена файлов)."""
    if not os.path.isdir(SAVES_DIR):
        return []
    return sorted(
        f for f in os.listdir(SAVES_DIR)
        if f.endswith(".json")
    )


def export_to_csv(game: Game, path: str) -> str:
    """Экспортирует все броски игры в CSV для анализа."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "player", "dice_type", "num_dice",
            "values", "modifier", "total"
        ])
        for r in game.dice_roller.history:
            writer.writerow([
                r.timestamp.isoformat(),
                r.player_name or "",
                r.dice_type,
                r.num_dice,
                " ".join(str(v) for v in r.values),
                r.modifier,
                r.total,
            ])
    return path
