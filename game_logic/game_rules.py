"""
Базовый класс правил игры и контроллер игры.
Конкретные игры (Пятитысяч, Покер на костях и т.п.) наследуются от GameRules.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from game_logic.dice import DiceRoller, RollResult
from game_logic.player import Player, PLAYER_COLORS


@dataclass
class TurnResult:
    """Что вернул раунд игры после броска."""
    roll: RollResult
    points: int
    combination: str = ""        # например, "Фулл-хаус"
    extra: Dict[str, Any] = field(default_factory=dict)


class GameRules(ABC):
    """
    Абстрактный базовый класс правил игры.

    Чтобы добавить новую игру:
    1. Создайте подкласс GameRules.
    2. Переопределите calculate_points() и метаданные.
    3. Зарегистрируйте игру в presets/__init__.py.
    """

    name: str = "Базовая игра"
    description: str = ""
    num_dice: int = 5            # сколько кубиков бросает игрок за ход
    dice_type: str = "D6"        # тип кубика
    target_score: int = 100      # целевые очки для победы
    max_rounds: Optional[int] = None  # если задано — игра ограничена раундами

    @abstractmethod
    def calculate_points(self, roll: RollResult) -> TurnResult:
        """
        Расчёт очков на основе результата броска.
        Должен быть переопределён в подклассах.
        """
        ...

    def check_victory(self, players: List[Player]) -> Optional[Player]:
        """
        Проверка условий победы. По умолчанию: первый, кто достиг target_score.
        Можно переопределить (например, минимум очков, или по раундам).
        """
        for player in players:
            if player.score >= self.target_score:
                return player
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация настроек правил."""
        return {
            "name": self.name,
            "num_dice": self.num_dice,
            "dice_type": self.dice_type,
            "target_score": self.target_score,
            "max_rounds": self.max_rounds,
        }


# -------- Контроллер игры --------

class Game:
    """
    Основной класс, управляющий ходом игры.
    Связывает правила, игроков и кубики.
    """

    def __init__(self, rules: GameRules):
        self.rules = rules
        self.players: List[Player] = []
        self.dice_roller = DiceRoller()
        self.current_player_index = 0
        self.round_number = 1
        self.winner: Optional[Player] = None
        self.history: List[str] = []   # текстовый журнал событий
        self.created_at = datetime.now()
        self._auto_save_every: int = 5  # автосохранение каждые N ходов
        self._turns_since_save: int = 0

    # ------------ Игроки ------------

    def add_player(self, name: str) -> Player:
        """Добавить игрока (2..8)."""
        if len(self.players) >= 8:
            raise ValueError("Максимум 8 игроков")
        if any(p.name == name for p in self.players):
            raise ValueError(f"Игрок с именем «{name}» уже существует")
        color = PLAYER_COLORS[len(self.players) % len(PLAYER_COLORS)]
        player = Player(name=name.strip(), color=color)
        self.players.append(player)
        self._log(f"Добавлен игрок: {name}")
        return player

    def remove_player(self, name: str) -> bool:
        """Удалить игрока по имени. Вернёт True, если удалось."""
        for i, p in enumerate(self.players):
            if p.name == name:
                self.players.pop(i)
                # если текущий индекс выходит за пределы — корректируем
                if self.current_player_index >= len(self.players):
                    self.current_player_index = 0
                self._log(f"Удалён игрок: {name}")
                return True
        return False

    @property
    def current_player(self) -> Optional[Player]:
        if not self.players:
            return None
        return self.players[self.current_player_index]

    def next_player(self) -> Optional[Player]:
        """Передать ход следующему игроку. Возвращает нового текущего игрока."""
        if not self.players:
            return None
        self.current_player_index = (
            (self.current_player_index + 1) % len(self.players)
        )
        # Если круг прошёл — увеличиваем номер раунда
        if self.current_player_index == 0:
            self.round_number += 1
            self._log(f"Начался раунд {self.round_number}")
        return self.current_player

    # ------------ Игровой процесс ------------

    def roll_dice(
        self,
        num_dice: Optional[int] = None,
        dice_type: Optional[str] = None,
        modifier: int = 0,
    ) -> TurnResult:
        """
        Выполнить бросок для текущего игрока и подсчитать очки по правилам.
        """
        if self.winner is not None:
            raise RuntimeError("Игра уже окончена")
        if not self.players:
            raise RuntimeError("Нет игроков")

        num_dice = num_dice if num_dice is not None else self.rules.num_dice
        dice_type = dice_type if dice_type is not None else self.rules.dice_type
        player = self.current_player

        roll = self.dice_roller.roll(
            num_dice=num_dice,
            dice_type=dice_type,
            modifier=modifier,
            player_name=player.name,
        )
        player.add_roll(roll)

        turn = self.rules.calculate_points(roll)
        player.add_score(turn.points)
        log_entry = (
            f"Раунд {self.round_number}: {player.name} бросил {roll} → "
            f"{turn.combination or 'обычный бросок'} ({turn.points:+d} очков, "
            f"итого {player.score})"
        )
        player.add_turn_log(log_entry)
        self._log(log_entry)

        # проверить победу
        winner = self.rules.check_victory(self.players)
        if winner is not None:
            self.winner = winner
            self._log(f"🏆 Победитель: {winner.name} ({winner.score} очков)")

        self._turns_since_save += 1
        return turn

    def reset(self) -> None:
        """Сбросить состояние игры, оставив тех же игроков."""
        for p in self.players:
            p.reset()
        self.dice_roller.clear_history()
        self.current_player_index = 0
        self.round_number = 1
        self.winner = None
        self.history.clear()
        self._turns_since_save = 0
        self._log("Игра перезапущена")

    def get_winner(self) -> Optional[Player]:
        """Текущий победитель (или None, если игра не окончена)."""
        return self.winner

    def get_leaderboard(self) -> List[Player]:
        """Игроки, отсортированные по убыванию очков."""
        return sorted(self.players, key=lambda p: p.score, reverse=True)

    # ------------ Сериализация ------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rules": self.rules.to_dict(),
            "rules_class": self.rules.__class__.__name__,
            "players": [p.to_dict() for p in self.players],
            "current_player_index": self.current_player_index,
            "round_number": self.round_number,
            "winner_name": self.winner.name if self.winner else None,
            "history": list(self.history),
            "created_at": self.created_at.isoformat(),
        }

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history.append(f"[{timestamp}] {message}")
