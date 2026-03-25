#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# ==== Настройки ====
FILE_PATH = "SETTINGS.py"   # путь к файлу с ПРЯМЫМИ слэшами
KEY_NAME  = "B_RELOAD_ORDER"     # имя ключа в YAML
NEW_VALUE = "on"             # слово для записи (будет без кавычек)
# ===================

def main():
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        text = ""

    key_regex = re.escape(KEY_NAME)

    # Заменяем только значение у KEY_NAME, сохраняя отступы и комментарий.
    # Если перед комментарием нет пробела — добавим один.
    pattern = re.compile(
        rf'^(?P<indent>[ \t]*){key_regex}[ \t]*=[ \t]*'
        r'(?P<value>[^#\r\n]*)'
        r'(?P<space_before_comment>[ \t]*)'
        r'(?P<comment>#.*)?$',
        re.MULTILINE
    )

    def repl(m):
        indent = m.group("indent") or ""
        space = m.group("space_before_comment") or ""
        comment = m.group("comment") or ""
        if comment and space == "":
            space = " "
        return f"{indent}{KEY_NAME} = {NEW_VALUE}{space}{comment}"

    new_text, replaced_count = pattern.subn(repl, text, count=1)

    # Если ключа не было — добавим его в конец файла
    if replaced_count == 0:
        if new_text and not new_text.endswith("\n"):
            new_text += "\n"
        new_text += f"{KEY_NAME} = {NEW_VALUE}\n"

    with open(FILE_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)

if __name__ == "__main__":
    main()
