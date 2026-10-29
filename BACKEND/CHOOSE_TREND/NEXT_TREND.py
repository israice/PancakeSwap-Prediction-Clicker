
import os
import sys
import re
from pathlib import Path


# ==================== КОНСТАНТЫ НАСТРОЕК ====================

PROJECT_ROOT = "./"
DASHBOARD_FILE = "DASHBOARD.py"
FILE_ENCODING = "utf-8"

VARIABLE_TREND_NEEDED_UP_COLOR = "TREND_NEEDED_UP_COLOR"
VARIABLE_GET_TREND_COLOR = "GET_TREND_COLOR"
VARIABLE_NEXT_TREND = "NEXT_TREND"

TREND_UP_VALUE = "UP"
TREND_DOWN_VALUE = "DOWN"


# ==================== ОТКЛЮЧЕНИЕ BYTECODE ====================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ==================== ФУНКЦИИ ====================

def get_dashboard_path():
    return Path(PROJECT_ROOT) / DASHBOARD_FILE


def read_variable(source, variable_name):
    pattern = (
        r"^[ \t]*"
        + re.escape(variable_name)
        + r"[ \t]*=[ \t]*(['\"])(.*?)\1"
    )

    match = re.search(pattern, source, re.MULTILINE)

    if match is None:
        return None

    return match.group(2)


def update_next_trend(source, trend):
    pattern = (
        r"^([ \t]*"
        + re.escape(VARIABLE_NEXT_TREND)
        + r"[ \t]*=[ \t]*)(['\"])(.*?)(\2)"
    )

    replacement = lambda match: (
        match.group(1)
        + match.group(2)
        + trend
        + match.group(4)
    )

    updated_source, count = re.subn(
        pattern,
        replacement,
        source,
        count=1,
        flags=re.MULTILINE,
    )

    if count:
        return updated_source

    newline = "\r\n" if "\r\n" in source else "\n"

    if source and not source.endswith(("\n", "\r")):
        source += newline

    return source + f'{VARIABLE_NEXT_TREND} = "{trend}"{newline}'


def main():
    dashboard_path = get_dashboard_path()

    try:
        source = dashboard_path.read_text(encoding=FILE_ENCODING)

        up_color = read_variable(
            source,
            VARIABLE_TREND_NEEDED_UP_COLOR,
        )
        current_color = read_variable(
            source,
            VARIABLE_GET_TREND_COLOR,
        )

        if up_color is None or current_color is None:
            return

        trend = (
            TREND_UP_VALUE
            if up_color == current_color
            else TREND_DOWN_VALUE
        )

        updated_source = update_next_trend(source, trend)

        if updated_source != source:
            dashboard_path.write_text(
                updated_source,
                encoding=FILE_ENCODING,
                newline="",
            )

    except (OSError, KeyboardInterrupt):
        return


if __name__ == "__main__":
    main()
