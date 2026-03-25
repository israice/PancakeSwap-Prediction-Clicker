import subprocess
import sys

# ================= НАСТРОЙКИ =================
SETTINGS_FILE = "SETTINGS.py"
YAML_KEY_RUNNER = "STRATEGY_GO_WITH_FLOW"
RUNNER_ON_VALUE = "DISABLE"

MAIN_SCRIPTS = [
    {"print": "STRATEGY_GO_WITH_FLOW - DISABLED..."},
    "BACKEND/D_FLOW/B_RELOAD_ORDER/tools/click_CHECK_CANDLE_COLOR_go_disabled.py",
]


def load_settings():
    """Читаем настройки из файла SETTINGS.py"""
    settings = {}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        exec(f.read(), settings)
    return settings


def is_runner_on(value) -> bool:
    """Проверка YAML_KEY_RUNNER (строка или bool)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == RUNNER_ON_VALUE.lower()
    return False


def run_script(script):
    """Запускает один шаг (print или python-скрипт)"""
    if isinstance(script, dict) and "print" in script:
        print(script["print"])
    elif isinstance(script, str):
        print(f"=== RUN {script} ===")
        subprocess.run(["python", script], check=False)
    else:
        print(f"[WARN] Неверный тип шага: {script}")


def run_script_list(scripts):
    """Выполняем список шагов по очереди"""
    for i, script in enumerate(scripts, start=1):
        run_script(script)


def main():
    """Одиночный запуск"""
    settings = load_settings()
    if is_runner_on(settings.get(YAML_KEY_RUNNER, "")):
        run_script_list(MAIN_SCRIPTS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
