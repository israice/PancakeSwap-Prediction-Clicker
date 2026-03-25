#!/usr/bin/env python3
# do_delay_silent.py

import time
import sys

# === НАСТРОЙКИ ===
SETTINGS_PATH = "SETTINGS.py"          # путь к YAML
KEY = "SYSTEM_SMALL_DELAY_IN_SECONDS"          # ключ с количеством секунд

def read_delay(path: str, key: str) -> float:
    """Читает секунды из SETTINGS.py. Поддерживает комментарии после #."""
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            left, sep, right = line.partition("=")
            if not sep:
                continue
            if left.strip() == key:
                value_str = right.split("#", 1)[0].strip()
                delay = float(value_str)  # допускаем дробные секунды
                if delay < 0:
                    raise ValueError("negative")
                return delay
    raise KeyError("missing_key")

def safe_sleep(seconds: float) -> None:
    """Пауза с короткими тиками; Ctrl+C прерывает без вывода сообщений."""
    end = time.monotonic() + seconds
    try:
        while True:
            remain = end - time.monotonic()
            if remain <= 0:
                return
            time.sleep(min(0.1, remain))
    except KeyboardInterrupt:
        # тихо выходим без сообщений
        pass

if __name__ == "__main__":
    try:
        delay = read_delay(SETTINGS_PATH, KEY)
        safe_sleep(delay)
    except KeyboardInterrupt:
        # на всякий случай — тоже тихо
        pass
    except Exception:
        # любые другие ошибки — тихий выход с кодом 1
        sys.exit(1)
