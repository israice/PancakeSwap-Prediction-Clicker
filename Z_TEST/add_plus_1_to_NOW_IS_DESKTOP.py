
import os
import re
import sys

# ============ НАСТРОЙКИ ============
# Все пути — от корня проекта, только с прямыми слешами
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DASHBOARD_FILE = "DASHBOARD.py"

# Какую переменную увеличить
VARIABLE_NAME = "NOW_IS_DESKTOP"

# Символ операции над значением переменной (+ или -)
ADD_SYMBOL = "+"

# Число, которое прибавляется к значению переменной
ADD_VALUE = 1
# ===================================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def get_dashboard_path():
    """Путь к DASHBOARD.py от корня проекта (прямые слеши -> реальный путь)."""
    return os.path.join(PROJECT_ROOT, DASHBOARD_FILE.replace("/", os.sep))


def read_dashboard(path):
    """Читаем DASHBOARD.py (utf-8, ошибки не роняют скрипт)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def increment_variable(text, variable_name):
    """Ищем VARIABLE_NAME = <число> и меняем на число + ADD_VALUE (или -).

    Знак берётся из константы ADD_SYMBOL ("+" или "-"),
    величина сдвига — из константы ADD_VALUE.

    Возвращает новый текст или None, если значение не число.
    """
    pattern = r"^(\s*" + re.escape(variable_name) + r"\s*=\s*)(-?\d+)(\s*(?:#.*)?)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        return None
    if ADD_SYMBOL == "-":
        new_value = str(int(match.group(2)) - ADD_VALUE)
    else:
        new_value = str(int(match.group(2)) + ADD_VALUE)
    return text[: match.start()] + match.group(1) + new_value + match.group(3) + text[match.end():]


def variable_exists(text, variable_name):
    """True, если переменная объявлена в файле (VARIABLE_NAME = ...)."""
    pattern = r"^\s*" + re.escape(variable_name) + r"\s*=\s*(.+)$"
    return re.search(pattern, text, flags=re.MULTILINE) is not None


def write_dashboard(path, text):
    """Записываем обновлённый DASHBOARD.py."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def add_plus_1_to_NOW_IS_DESKTOP():
    """+1 к переменной в DASHBOARD.py (NOW_IS_DESKTOP = 1 -> 2).

    Сдвиг задаётся константами ADD_SYMBOL и ADD_VALUE из настроек.
    При ошибке — сообщение в консоль (stderr).
    """
    path = get_dashboard_path()
    if not os.path.isfile(path):
        print(f"[ERR] Файл не найден: {path}", file=sys.stderr)
        return

    old_text = read_dashboard(path)

    if not variable_exists(old_text, VARIABLE_NAME):
        print(f"[ERR] Переменная {VARIABLE_NAME} не найдена в {path}", file=sys.stderr)
        return

    new_text = increment_variable(old_text, VARIABLE_NAME)
    if new_text is None:
        print(f"[ERR] {VARIABLE_NAME} не является числом в {path}", file=sys.stderr)
        return

    write_dashboard(path, new_text)


def main():
    """Одиночный запуск"""
    add_plus_1_to_NOW_IS_DESKTOP()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl + C — дополнительная остановка
        sys.exit(0)
