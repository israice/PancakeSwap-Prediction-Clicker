#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

# ==== Настройки ====
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # корень проекта
FILE_PATH = PROJECT_ROOT + "/DASHBOARD.py"   # путь с прямыми слэшами от корня проекта
NOW_KEY_NAME = "NOW_IS_DESKTOP"              # ключ, который заменяем на 0
MAX_KEY_NAME = "HOW_MUCH_DESKTOPS"           # ключ для сравнения
# ===================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def get_key_value(text, key_name):
    # Ищет строку "KEY = value" вне зависимости от отступа, сохраняет группу значения.
    pattern = re.compile(
        rf'^(?P<indent>[ \t]*){re.escape(key_name)}[ \t]*=[ \t]*'
        r'(?P<value>[^#\r\n]*?)'
        r'(?P<tail>[ \t]*(?:#.*)?)$',
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        return None
    return m.group("value").strip()


def normalize(value):
    # "4" / " 4 " / "'4'" -> "4" для сравнения
    return str(value).strip().strip("'\"")


def compare_values(now_value, max_value):
    # Сравнивает значения как числа, если оба числовые; иначе — как строки.
    try:
        return int(normalize(now_value)) - int(normalize(max_value))
    except ValueError:
        a, b = normalize(now_value), normalize(max_value)
        return 0 if a == b else (1 if a > b else -1)


def run():
    text = read_text(FILE_PATH)
    if text is None:
        return

    now_value = get_key_value(text, NOW_KEY_NAME)
    max_value = get_key_value(text, MAX_KEY_NAME)

    # Заменяем только если оба ключа найдены и NOW_IS_DESKTOP выше HOW_MUCH_DESKTOPS
    if now_value is None or max_value is None:
        return
    if not (compare_values(now_value, max_value) > 0):
        return

    key_regex = re.escape(NOW_KEY_NAME)
    pattern = re.compile(
        rf'^(?P<indent>[ \t]*){key_regex}[ \t]*=[ \t]*'
        r'(?P<value>[^#\r\n]*)'
        r'(?P<space_before_comment>[ \t]*)'
        r'(?P<comment>#.*)?$',
        re.MULTILINE,
    )

    def repl(m):
        indent = m.group("indent") or ""
        space = m.group("space_before_comment") or ""
        comment = m.group("comment") or ""
        if comment and space == "":
            space = " "
        return f"{indent}{NOW_KEY_NAME} = 0{space}{comment}"

    new_text, replaced_count = pattern.subn(repl, text, count=1)

    # Ключ найден выше, но перестраховка: пишем файл только если была замена
    if replaced_count == 0:
        return

    with open(FILE_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)


def main():
    try:
        run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
