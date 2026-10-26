
import os
import sys
import time
import re
from pathlib import Path

# ==================== НАСТРОЙКИ ====================

DASHBOARD_PATH = "DASHBOARD.py"
UPDATE_INTERVAL = 1.0

# ==================== ОТКЛЮЧЕНИЕ BYTECODE ====================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# ==================== ФУНКЦИИ ====================

def get_dashboard_path():
    """Возвращает путь к DASHBOARD.py от корня проекта."""
    return Path(__file__).resolve().parents[2] / DASHBOARD_PATH  # ROUND_TIME -> BACKEND -> корень


def read_time_left(file_path):
    """Читает существующее значение TIME_LEFT из файла."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    match = re.search(
        r"(?m)^(\s*TIME_LEFT\s*=\s*)(\d+)\.(\d{1,2})(\s*(?:#.*)?$)",
        content,
    )

    if not match:
        raise ValueError("Переменная TIME_LEFT не найдена.")

    minutes = int(match.group(2))
    seconds = int(match.group(3))

    if seconds > 59:
        raise ValueError("Некорректный формат TIME_LEFT.")

    return content, match, minutes * 60 + seconds


def update_time_left(file_path, content, match, total_seconds):
    """Обновляет TIME_LEFT непосредственно в файле."""
    minutes, seconds = divmod(total_seconds, 60)
    new_value = f"{minutes}.{seconds:02d}"

    updated_content = (
        content[:match.start(2)]
        + new_value
        + content[match.end(3):]
    )

    with open(file_path, "w", encoding="utf-8", newline="") as file:
        file.write(updated_content)


def main():
    file_path = get_dashboard_path()

    try:
        content, match, total_seconds = read_time_left(file_path)

        while total_seconds > 0:
            time.sleep(UPDATE_INTERVAL)

            content, match, current_seconds = read_time_left(file_path)

            total_seconds = max(0, current_seconds - 1)

            update_time_left(
                file_path,
                content,
                match,
                total_seconds,
            )

    except KeyboardInterrupt:
        return


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    main()
