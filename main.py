"""
Симулятор настольных игр с вероятностными моделями.
Точка входа в приложение.

Запуск: python main.py
"""
import sys
import os

# Добавляем корневую директорию в путь импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from utils.logger import setup_logger


def main():
    """Запуск приложения."""
    logger = setup_logger()
    logger.info("Запуск симулятора настольных игр")

    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        raise
    finally:
        logger.info("Завершение работы приложения")


if __name__ == "__main__":
    main()
