
import os
import re
import sys
from pathlib import Path


# ==================== КОНСТАНТЫ НАСТРОЕК ====================

TIME_LEFT_SIGN = "+"  # Знак изменения: "+" или "-"
TIME_LEFT_CHANGE = 1  # Величина изменения

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_FILE = PROJECT_ROOT / "DASHBOARD.py"


# ==================== СИСТЕМНЫЕ НАСТРОЙКИ ====================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ==================== ФУНКЦИИ ====================

def change_time_left() -> None:
    """Изменяет целую часть TIME_LEFT на заданную величину."""

    if TIME_LEFT_SIGN not in ("+", "-"):
        raise ValueError('TIME_LEFT_SIGN должен быть "+" или "-".')

    if TIME_LEFT_CHANGE < 0:
        raise ValueError("TIME_LEFT_CHANGE не может быть отрицательным.")

    file_path = DASHBOARD_FILE

    if not file_path.is_file():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    pattern = (
        r"(?m)^(\s*TIME_LEFT\s*=\s*)"
        r"(\d+)"
        r"(\.\d+)?"
        r"(\s*(?:#.*)?)$"
    )

    match = re.search(pattern, content)

    if not match:
        raise ValueError(
            "Переменная TIME_LEFT не найдена "
            "или имеет неверный формат."
        )

    integer_part = int(match.group(2))
    decimal_part = match.group(3) or ""
    trailing_part = match.group(4)

    change = TIME_LEFT_CHANGE
    if TIME_LEFT_SIGN == "-":
        change = -change

    new_integer_part = integer_part + change

    if new_integer_part < 0:
        new_integer_part = 0

    new_value = (
        f"{match.group(1)}"
        f"{new_integer_part}"
        f"{decimal_part}"
        f"{trailing_part}"
    )

    updated_content = (
        content[:match.start()]
        + new_value
        + content[match.end():]
    )

    file_path.write_text(updated_content, encoding="utf-8")


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    change_time_left()
