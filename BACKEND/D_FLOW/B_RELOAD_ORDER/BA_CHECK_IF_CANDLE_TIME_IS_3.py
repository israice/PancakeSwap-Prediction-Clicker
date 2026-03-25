#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from pathlib import Path

# ================== НАСТРОЙКИ (ТОЛЬКО ПРЯМЫЕ СЛЭШИ) ==================
SETTINGS_PATH       = "SETTINGS.py"   # путь к файлу
TIME_KEY            = "CANDLE_TIME"       # имя ключа с временем
FLAG_KEY            = "CHECK_IF_CANDLE_TIME_IS_3"  # имя флага для записи результата
TARGET_DIGIT        = "3"                 # целевая цифра для сравнения
HOUR_DIGIT_INDEX    = 1                   # индекс цифры в часах: 0=десятки, 1=единицы

TRUE_WORD           = "true"              # что писать, если совпало
FALSE_WORD          = "false"             # что писать, если не совпало
# =====================================================================

def read_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"Файл не найден: {path}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8")

def write_text_preserving_newlines(path: str, new_text: str) -> None:
    Path(path).write_text(new_text, encoding="utf-8", newline="")

def detect_newline(s: str) -> str:
    return "\r\n" if "\r\n" in s else "\n"

def find_key_line(text: str, key: str):
    """
    Возвращает match с группами:
    pre — всё до значения (включая "KEY:" и пробелы),
    val — само значение (до комментария),
    post — остальная часть строки (комментарии, пробелы) до конца строки.
    """
    pattern = re.compile(
        rf'^(?P<pre>\s*{re.escape(key)}\s*=\s*)(?P<val>[^#\r\n]*?)(?P<post>\s*(?:#[^\r\n]*)?)$',
        flags=re.MULTILINE
    )
    return pattern.search(text), pattern

def extract_time_value(text: str, key: str) -> str:
    m, _ = find_key_line(text, key)
    if not m:
        print(f"Ключ {key} не найден в файле.", file=sys.stderr)
        sys.exit(1)
    raw = m.group("val").strip()
    # уберём кавычки, если есть
    if len(raw) >= 2 and ((raw[0] == raw[-1] == '"') or (raw[0] == raw[-1] == "'")):
        raw = raw[1:-1]
    if ":" not in raw:
        print(f"Некорректный формат времени в {key}: '{raw}'. Ожидается HH:MM.", file=sys.stderr)
        sys.exit(1)
    return raw

def get_hour_digit(time_str: str, index: int) -> str:
    """
    Возвращает цифру часов по индексу 0/1. '9:05' -> часы '09'.
    """
    hh = time_str.split(":", 1)[0].strip()
    if not hh:
        return ""
    hh2 = hh.zfill(2)
    if index < 0 or index >= len(hh2):
        print(f"Индекс {index} вне диапазона для часов '{hh2}'.", file=sys.stderr)
        sys.exit(1)
    return hh2[index]

def render_with_original_quoting(original_value: str, new_plain: str) -> str:
    """
    Если исходное значение было в кавычках — сохраняем тип кавычек.
    Иначе пишем как есть.
    """
    orig = original_value.strip()
    if len(orig) >= 2 and ((orig[0] == orig[-1] == '"') or (orig[0] == orig[-1] == "'")):
        quote = orig[0]
        return f"{quote}{new_plain}{quote}"
    return new_plain

def upsert_flag_value(text: str, key: str, new_value_str: str) -> str:
    """
    Заменяет только значение (с учётом исходных кавычек), сохраняя положение строки,
    отступы, двоеточие и комментарии после значения. Если ключа нет — добавляет в конец.
    """
    m, pattern = find_key_line(text, key)
    if m:
        pre, old_val, post = m.group("pre"), m.group("val"), m.group("post")
        replacement_val = render_with_original_quoting(old_val, new_value_str)
        new_line = f"{pre}{replacement_val}{post}"
        start, end = m.span()
        return text[:start] + new_line + text[end:]

    # Ключа нет — добавим аккуратно в конец
    nl = detect_newline(text)
    comment = f"# {TRUE_WORD}/{FALSE_WORD}" if TRUE_WORD or FALSE_WORD else ""
    suffix = f"{key} = {new_value_str} {comment}".rstrip()
    if text.endswith(("\n", "\r", "\r\n")):
        return text + suffix + nl
    else:
        return text + nl + suffix + nl

def main() -> None:
    txt = read_text(SETTINGS_PATH)

    # читаем время
    time_val = extract_time_value(txt, TIME_KEY)

    # берём нужную цифру часов по индексу
    digit = get_hour_digit(time_val, HOUR_DIGIT_INDEX)

    # сравниваем с целевой цифрой
    is_match = (digit == TARGET_DIGIT)

    # какое слово писать
    out_word = TRUE_WORD if is_match else FALSE_WORD

    # обновляем/добавляем флаг
    new_txt = upsert_flag_value(txt, FLAG_KEY, out_word)

    # пишем назад
    write_text_preserving_newlines(SETTINGS_PATH, new_txt)

if __name__ == "__main__":
    main()
