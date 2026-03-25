import subprocess
import yaml
import sys

# ================= НАСТРОЙКИ =================
SETTINGS_FILE = "BACKEND/Y_DATA/A_runners.yaml"
YAML_KEY_RUNNER = "RUNNER_PRE_RESET"
RUNNER_ON_VALUE = "on"

MAIN_SCRIPTS = [
    {"print": "PRE RESET..."},
    "BACKEND/B_RESET/tools/reset_ALL_ROUNDS_COUNTER.py",
    "BACKEND/B_RESET/tools/get_METAMASK_BNB_BALANCE.py",
    "BACKEND/B_RESET/tools/create_INSERT_AMMOUNT_IN_BNB.py",
    # ################################
    "BACKEND/B_RESET/tools/disable_PRE_RESET.py",
]
# ==============================================


def load_settings():
    """Читаем настройки из файла SETTINGS.py"""
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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
