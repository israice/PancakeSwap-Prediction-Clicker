
import os
import re
import sys
from pathlib import Path


# ==================== КОНСТАНТЫ НАСТРОЕК ====================

TIME_LEFT_SIGN = "-"  # Знак изменения: "+" или "-"
# Величина изменения. Формат как в DASHBOARD.py: M.SS.
# Примеры: 1 = 1 минута, "1.30" = 1 минута 30 секунд, "0.45" = 45 секунд.
TIME_LEFT_CHANGE = "1.50"

# Величина плюса (страховка ниже, в change_time_left): если TIME_LEFT меньше
# вычитаемой величины и вычитать уже нечего, вместо минуса применяется ЭТОТ плюс.
# Формат такой же: M.SS.
TIME_LEFT_PLUS_CHANGE = "1.00"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_FILE = PROJECT_ROOT / "DASHBOARD.py"


# ==================== СИСТЕМНЫЕ НАСТРОЙКИ ====================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ==================== ФУНКЦИИ ====================

TIME_LEFT_CHANGE_RE = re.compile(r"^(\d+)(?:\.([0-5]\d|[0-9]))?$")


def parse_time_change(value, name: str) -> int:
    """Преобразует значение M.SS в общее количество секунд.

    Поддерживаются целые минуты (1 или "1") и формат минуты.секунды
    ("1.30" = 1 минута 30 секунд, "0.45" = 45 секунд). Дробные числа float
    намеренно не поддерживаются: 1.30 в Python превращается в 1.3 и приводит
    к неверному времени.
    """

    if isinstance(value, bool):
        raise TypeError(f'{name}: булево значение недопустимо. Используй "1.30".')

    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{name} не может быть отрицательным.")
        return value * 60

    if isinstance(value, float):
        raise TypeError(
            f'{name}: float недопустим из-за неоднозначности формата. '
            f'Используй строку, например "1.30".'
        )

    if not isinstance(value, str):
        raise TypeError(f'{name}: ожидается int или строка формата "M.SS".')

    text = value.strip()
    match = TIME_LEFT_CHANGE_RE.fullmatch(text)

    if not match:
        raise ValueError(
            f'{name}: неверный формат {value!r}. '
            f'Ожидается M или M.SS, например "1", "1.30", "0.45". '
            f'Секунды должны быть от 00 до 59.'
        )

    minutes = int(match.group(1))
    seconds_text = match.group(2) or "0"
    seconds = int(seconds_text.ljust(2, "0"))

    return minutes * 60 + seconds


def format_time_left(total_seconds: int) -> str:
    """Преобразует секунды в формат M.SS для DASHBOARD.py."""

    if total_seconds < 0:
        raise ValueError("total_seconds не может быть отрицательным.")

    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}.{seconds:02d}"


def change_time_left() -> None:
    """Изменяет TIME_LEFT на заданную величину."""

    if TIME_LEFT_SIGN not in ("+", "-"):
        raise ValueError('TIME_LEFT_SIGN должен быть "+" или "-".')

    change_seconds = parse_time_change(TIME_LEFT_CHANGE, "TIME_LEFT_CHANGE")
    plus_change_seconds = parse_time_change(TIME_LEFT_PLUS_CHANGE, "TIME_LEFT_PLUS_CHANGE")

    if TIME_LEFT_SIGN == "-":
        signed_change = -change_seconds
    else:
        signed_change = change_seconds

    file_path = DASHBOARD_FILE

    if not file_path.is_file():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    pattern = (
        r"(?m)^(\s*TIME_LEFT\s*=\s*)"
        r"(\d+)"
        r"(?:\.(\d{1,2}))?"
        r"(\s*(?:#.*)?)$"
    )

    match = re.search(pattern, content)

    if not match:
        raise ValueError(
            "Переменная TIME_LEFT не найдена "
            "или имеет неверный формат."
        )

    integer_part = int(match.group(2))
    seconds_part = match.group(3) or "0"

    if len(seconds_part) == 1:
        seconds_part = seconds_part + "0"

    decimal_seconds = int(seconds_part)

    if decimal_seconds > 59:
        raise ValueError("Некорректный формат TIME_LEFT: секунды больше 59.")

    trailing_part = match.group(4)
    current_seconds = integer_part * 60 + decimal_seconds

    new_total_seconds = current_seconds + signed_change

    # Минус невозможен, если из TIME_LEFT нечего вычитать.
    # Тогда и только тогда применяем плюс (TIME_LEFT_PLUS_CHANGE).
    if TIME_LEFT_SIGN == "-" and new_total_seconds < 0:
        new_total_seconds = current_seconds + plus_change_seconds

    new_value = (
        f"{match.group(1)}"
        f"{format_time_left(new_total_seconds)}"
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
