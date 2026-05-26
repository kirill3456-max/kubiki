"""
Простой настраиваемый логгер для приложения.
"""
import logging
import os
import sys


def setup_logger(name: str = "game_simulator", level: int = logging.INFO) -> logging.Logger:
    """Настраивает корневой логгер приложения и возвращает его."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # уже настроен

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # файловый вывод (рядом с приложением)
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "app.log"), encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        # если нет прав на запись — просто пропускаем
        pass

    return logger


def get_logger(name: str = "game_simulator") -> logging.Logger:
    """Получить уже настроенный логгер."""
    return logging.getLogger(name)
