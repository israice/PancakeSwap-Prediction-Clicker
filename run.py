import subprocess
import time
import yaml
import sys

# ================= НАСТРОЙКИ =================
SETTINGS_FILE = "BACKEND/Y_DATA/A_runners.yaml"
YAML_KEY_RUNNER = "RUNNER_SYSTEM"
RUNNER_ON_VALUE = "on"

MAIN_SCRIPTS = [
    "BACKEND/B_RESET/A_run.py",
    # "BACKEND/D_FLOW/A_RELOAD_ALL/A_run.py",
    "BACKEND/D_FLOW/B_RELOAD_ORDER/B_run.py",
]

SCRIPTS_FINALIZATION = [
    "BACKEND/G_FITALATY/G_run.py",
]
# ==============================================


def load_settings():
    """Читаем настройки из файла SETTINGS.py"""
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_runner_on(value) -> bool:
    """
    Универсальная проверка YAML_KEY_RUNNER.
    Поддерживает строки и булевы значения.
    """
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
        subprocess.run(["python", script], check=False)
    else:
        print(f"[WARN] Неверный тип шага: {script}")


def run_script_list(scripts):
    """Выполняем список шагов по очереди"""
    for i, script in enumerate(scripts, start=1):
        run_script(script)


def main():
    """Основной цикл"""
    try:
        while True:
            settings = load_settings()
            if is_runner_on(settings.get(YAML_KEY_RUNNER, "")):
                run_script_list(MAIN_SCRIPTS)
            else:
                run_script_list(SCRIPTS_FINALIZATION)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Пользователь прервал выполнение (Ctrl+C).")
        print("→ Выполняем SCRIPTS_FINALIZATION...")
        run_script_list(SCRIPTS_FINALIZATION)
        sys.exit(0)


if __name__ == "__main__":
    main()
