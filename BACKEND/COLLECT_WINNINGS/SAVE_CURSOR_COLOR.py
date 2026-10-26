"""
Записывает HEX-цвет пикселя под курсором в переменную SAVE_CURSOR_COLOR файла test1.py.
"""

import ctypes
import ctypes.wintypes
import os
import re
import sys
import time

# --- Не создавать папки __pycache__ (bytecode-кэш) ---
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # корень проекта

# Целевой файл — от корня проекта, с прямыми слешами (как во всём проекте)
TARGET_FILE = "DASHBOARD.py"
TARGET_FILE = os.path.join(PROJECT_ROOT, TARGET_FILE.replace("/", os.sep))
INTERVAL = 0.2


def get_cursor_hex() -> str:
    """Возвращает цвет пикселя под курсором в формате #RRGGBB."""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    hdc = user32.GetDC(0)                       # DC всего экрана
    if not hdc:
        raise RuntimeError("Не удалось получить DC экрана")

    try:
        # Учитываем масштабирование Windows (DPI)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            user32.SetProcessDPIAware()

        pt = ctypes.wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))

        c = gdi32.GetPixel(hdc, pt.x, pt.y)
        if c == 0xFFFFFFFF:                      # CLR_INVALID
            raise RuntimeError("Не удалось прочитать пиксель")

        r = c & 0xFF
        g = (c >> 8) & 0xFF
        b = (c >> 16) & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    finally:
        user32.ReleaseDC(0, hdc)


def write_hex(hex_color: str) -> None:
    """Заменяет (или добавляет) SAVE_CURSOR_COLOR в test1.py."""
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            src = f.read()
    else:
        src = ""

    line = f'SAVE_CURSOR_COLOR = "{hex_color}"'
    pattern = re.compile(r"^(\s*SAVE_CURSOR_COLOR\s*=\s*).*$", re.MULTILINE)

    if pattern.search(src):
        src = pattern.sub(lambda m: m.group(1) + f'"{hex_color}"', src)
    else:
        if src and not src.endswith("\n"):
            src += "\n"
        src += line + "\n"

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(src)


def main() -> None:
    loop = "--loop" in sys.argv

    while True:
        hex_color = get_cursor_hex()
        write_hex(hex_color)
        print(hex_color)

        if not loop:
            break
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановлено.")