
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import pyautogui


SETTINGS_FILE = "DASHBOARD.py"
VAR_NAME = "INSERT_AMOUNT_IN_BNB"

# Паузы для приложений, которые не сразу принимают вставку.
TYPE_DELAY = 0.05


def load_value():
    """Читает значение переменной из SETTINGS.py."""

    path = SETTINGS_FILE

    if not os.path.isfile(path):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "SETTINGS.py",
        )

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Не найден файл настроек: {path}"
        )

    pattern = re.compile(
        rf"^\s*{re.escape(VAR_NAME)}\s*=\s*(.*?)\s*$"
    )

    with open(path, "r", encoding="utf-8-sig") as file:
        for line in file:
            match = pattern.match(line)

            if match:
                raw = match.group(1).split("#", 1)[0].strip()

                if (
                    len(raw) >= 2
                    and raw[0] == raw[-1]
                    and raw[0] in ("'", '"')
                ):
                    raw = raw[1:-1]

                if not raw:
                    raise ValueError(
                        f"{VAR_NAME} пустая"
                    )

                return raw

    raise ValueError(
        f"Переменная {VAR_NAME} не найдена"
    )


def paste_value(value):
    """Вставляет значение в поле, которое уже получило фокус."""

    # Вводим именно клавиатурой: некоторые web-поля/кошельки блокируют Ctrl+V.
    value = str(value)

    # Фокус полю уже передал предыдущий шаг AB_CLICK_ON_TEXT_AREA.py.
    # Ctrl+A не даёт дописать сумму к старому значению.
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.write(value, interval=TYPE_DELAY)

    print(f"Команда вставки отправлена. Значение: {value!r}")


def main():
    value = load_value()
    paste_value(value)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ОШИБКА: {exc}")
        sys.exit(1)
