import subprocess
import sys

# ================= НАСТРОЙКИ =================
SETTINGS_FILE = "SETTINGS.py"
YAML_KEY_RUNNER = "STRATEGY_TYPE"
RUNNER_ON_VALUE = "LONG"

MAIN_SCRIPTS = [
    {"print": "RELOAD ORDER..."},

    "BACKEND/D_FLOW/B_RELOAD_ORDER/tools/click_the_CHECK_IF_NEED_TO_CLOSE_PROMO_POPUP.py",    
        "BACKEND/D_FLOW/B_RELOAD_ORDER/tools/SYSTEM_SMALL_DELAY_IN_SECONDS.py",
    
    "BACKEND/D_FLOW/B_RELOAD_ORDER/BCAA_run_long.py",

    "BACKEND/D_FLOW/B_RELOAD_ORDER/BCAD_if_CANDLE_COLOR_is_GREEN.py",
    "BACKEND/D_FLOW/B_RELOAD_ORDER/BCAE_if_CANDLE_COLOR_is_RED.py",
    "BACKEND/D_FLOW/B_RELOAD_ORDER/BCAF_if_CANDLE_COLOR_is_ZERO.py",
    
    "BACKEND/D_FLOW/A_RELOAD_ALL/tools/enable_STRATEGY_TYPE_short.py",
    "BACKEND/Z_TOOLS/next_desktop.py",
]
# ==============================================


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
