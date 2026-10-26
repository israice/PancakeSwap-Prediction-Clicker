# -*- coding: utf-8 -*-
"""
Инкремент значения YAML-параметра без изменения остального содержимого файла.
"""

# ===== НАСТРОЙКИ =====
SETTINGS_PATH = "SETTINGS.py"  # путь к YAML-файлу (с прямыми слэшами)
KEY_NAME      = "ALL_ROUNDS_COUNTER"  # какой ключ увеличиваем
INCREMENT_BY  = 1                # на сколько увеличивать (целое число)
ENCODING      = "utf-8"          # кодировка файла
MAKE_BACKUP   = False            # создавать ли .bak копию перед записью (выкл)
# =====================

import re
import sys
from pathlib import Path
import shutil

def increment_yaml_key_value(
    file_path: str,
    key_name: str,
    delta: int = 1,
    encoding: str = "utf-8",
    make_backup: bool = False
) -> None:
    p = Path(file_path)

    if not p.exists():
        print(f"Файл не найден: {p}", file=sys.stderr)
        sys.exit(1)

    raw = p.read_bytes()
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as e:
        print(f"Не удалось декодировать файл как {encoding}: {e}", file=sys.stderr)
        sys.exit(1)

    pattern = re.compile(
        rf'^(?!\s*#)'
        rf'(?P<prefix>\s*{re.escape(key_name)}\s*=\s*)'
        rf'(?P<quote>["\']?)'
        rf'(?P<value>[+-]?\d+)'
        rf'(?P=quote)'
        rf'(?P<suffix>[^\r\n]*)',
        flags=re.MULTILINE
    )

    m = pattern.search(text)
    if not m:
        print(f"Ключ '{key_name}' не найден в файле {p}", file=sys.stderr)
        sys.exit(2)

    try:
        current = int(m.group("value"))
    except ValueError:
        print(f"Значение ключа '{key_name}' не является целым числом: {m.group('value')}", file=sys.stderr)
        sys.exit(3)

    new_value = str(current + delta)

    replacement = f"{m.group('prefix')}{m.group('quote')}{new_value}{m.group('quote')}{m.group('suffix')}"
    new_text = text[:m.start()] + replacement + text[m.end():]

    if new_text == text:
        print("Изменений нет — файл уже содержит нужное значение.")
        return

    if make_backup:
        shutil.copyfile(p, p.with_suffix(p.suffix + ".bak"))

    p.write_bytes(new_text.encode(encoding))

if __name__ == "__main__":
    increment_yaml_key_value(
        file_path=SETTINGS_PATH,
        key_name=KEY_NAME,
        delta=INCREMENT_BY,
        encoding=ENCODING,
        make_backup=MAKE_BACKUP
    )
