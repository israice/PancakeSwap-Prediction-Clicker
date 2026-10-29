
"""
Записывает HEX-цвет пикселя под курсором в целевую переменную Python-файла.

Запуск:
    python test.py            -> один снимок цвета
    python test.py --loop     -> постоянное обновление, Ctrl+C для остановки
"""

import ctypes
import ctypes.wintypes
import os
import re
import sys
import time
import signal
from pathlib import Path


# ==================== КОНСТАНТЫ НАСТРОЕК ====================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.as_posix()

TARGET_FILE = f"DASHBOARD.py"
TARGET_VARIABLE = "GET_TREND_COLOR"

INTERVAL = 0.2


# ==================== ОТКЛЮЧЕНИЕ BYTECODE ====================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ==================== ФУНКЦИИ ====================

def stop_handler(signum=None, frame=None) -> None:
    """Останавливает выполнение скрипта."""
    raise KeyboardInterrupt


def get_cursor_hex() -> str:
    """Возвращает цвет пикселя под курсором в формате #RRGGBB."""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass

    hdc = user32.GetDC(0)

    if not hdc:
        raise RuntimeError("Не удалось получить DC экрана")

    try:
        point = ctypes.wintypes.POINT()

        if not user32.GetCursorPos(ctypes.byref(point)):
            raise RuntimeError("Не удалось получить координаты курсора")

        color = gdi32.GetPixel(hdc, point.x, point.y)

        if color == 0xFFFFFFFF:
            raise RuntimeError("Не удалось прочитать пиксель")

        red = color & 0xFF
        green = (color >> 8) & 0xFF
        blue = (color >> 16) & 0xFF

        return f"#{red:02X}{green:02X}{blue:02X}"

    finally:
        user32.ReleaseDC(0, hdc)


def write_hex(hex_color: str) -> None:
    """Обновляет или добавляет целевую переменную в Python-файл."""
    if os.path.isfile(TARGET_FILE):
        with open(TARGET_FILE, "r", encoding="utf-8") as file:
            source = file.read()
    else:
        source = ""

    variable_name = re.escape(TARGET_VARIABLE)

    pattern = re.compile(
        rf"^[ \t]*{variable_name}[ \t]*=[ \t]*.*$",
        re.MULTILINE,
    )

    line = f'{TARGET_VARIABLE} = "{hex_color}"'

    if pattern.search(source):
        source = pattern.sub(lambda _: line, source, count=1)
    else:
        if source and not source.endswith("\n"):
            source += "\n"

        source += line + "\n"

    with open(TARGET_FILE, "w", encoding="utf-8", newline="") as file:
        file.write(source)


def main() -> None:
    """Основной цикл программы."""
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    loop = "--loop" in sys.argv

    while True:
        hex_color = get_cursor_hex()
        write_hex(hex_color)

        if not loop:
            break

        time.sleep(INTERVAL)


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, Exception):
        pass
