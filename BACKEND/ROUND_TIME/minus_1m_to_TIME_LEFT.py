
import os
import re
import sys
from pathlib import Path


# ==================== КОНСТАНТЫ НАСТРОЕК ====================

# DASHBOARD.py — от корня проекта; ROUND_TIME -> BACKEND -> корень (на два уровня выше)
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # корень проекта
DASHBOARD_FILE = PROJECT_ROOT / "DASHBOARD.py"


sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ==================== ФУНКЦИИ ====================

def decrease_time_left() -> None:
    """Уменьшает целую часть TIME_LEFT на 1, если она больше нуля."""

    file_path = DASHBOARD_FILE

    if not file_path.is_file():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    pattern = r"(?m)^(\s*TIME_LEFT\s*=\s*)(\d+)(\.\d+)(\s*(?:#.*)?)$"

    match = re.search(pattern, content)

    if not match:
        raise ValueError("Переменная TIME_LEFT не найдена или имеет неверный формат.")

    integer_part = int(match.group(2))
    decimal_part = match.group(3)

    if integer_part == 0:
        return

    new_value = (
        f"{match.group(1)}"
        f"{integer_part - 1}"
        f"{decimal_part}"
        f"{match.group(4)}"
    )

    updated_content = (
        content[:match.start()]
        + new_value
        + content[match.end():]
    )

    file_path.write_text(updated_content, encoding="utf-8")


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    decrease_time_left()
