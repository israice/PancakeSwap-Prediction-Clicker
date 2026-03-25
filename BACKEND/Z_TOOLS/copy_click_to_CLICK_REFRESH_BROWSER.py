# copy_value_in_yaml.py
# -*- coding: utf-8 -*-

import re
import sys

YAML_PATH = "SETTINGS.py"              # путь к файлу (только прямые слэши)
SRC_KEY   = "PIXEL_POINT"                # откуда копировать значение
DST_KEY   = "CLICK_REFRESH_BROWSER"         # куда вставить значение

def find_key_line(lines, key):
    """
    Ищет первую строку вида "<отступ><key>: <значение> [#коммент]"
    Возвращает (index, indent, value, comment, line_ending) или None.
    """
    # ^(\s*)(KEY)\s*:\s*(.*?)(\s*(#.*))?(\r?\n)?$
    pattern = re.compile(
        r'^(\s*)(' + re.escape(key) + r')\s*=\s*(.*?)(\s*(#.*))?(\r?\n)?$'
    )
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            indent = m.group(1) or ""
            # m.group(2) — сам ключ
            value = (m.group(3) or "").rstrip()     # значение без завершающих пробелов
            comment = m.group(5) or ""              # включая начальный пробел перед #, если был
            ending = m.group(6) if m.group(6) is not None else ("\n" if line.endswith("\n") else "")
            return i, indent, value, comment, ending
    return None


def main():
    try:
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Файл не найден: {YAML_PATH}", file=sys.stderr)
        sys.exit(1)

    src_info = find_key_line(lines, SRC_KEY)
    if not src_info:
        print(f"Ключ '{SRC_KEY}' не найден в {YAML_PATH}", file=sys.stderr)
        sys.exit(2)

    dst_info = find_key_line(lines, DST_KEY)
    if not dst_info:
        # Если целевого ключа нет — добавим новой строкой в конец файла
        # Отступ не ставим (верхний уровень), комментария нет.
        _, _, src_value, _, _ = src_info
        newline = "\n" if (len(lines) == 0 or lines[-1].endswith("\n")) else ""
        lines.append(f"{newline}{DST_KEY} = {src_value}\n")
        wrote = True
    else:
        # Заменяем только значение в целевой строке, сохраняя отступы, комментарий и перенос
        dst_idx, dst_indent, _, dst_comment, dst_end = dst_info
        _, _, src_value, _, _ = src_info

        lines[dst_idx] = f"{dst_indent}{DST_KEY} = {src_value}{dst_comment}{dst_end}"
        wrote = True

    if wrote:
        with open(YAML_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)


if __name__ == "__main__":
    main()
