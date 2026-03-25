import subprocess
import sys

# Запуск если значения переменных одинаковые 
SETTINGS_FILE = "SETTINGS.py"
YAML_KEY_MAIN = "MAXIMUM_ROUND_COUNTER_CONFIG"
# check if =
CONFIG_FILE = "SETTINGS.py"
YAML_KEY_CONFIG = "MAXIMUM_ROUND_COUNTER"

MAIN_SCRIPTS = [
    "BACKEND/D_FLOW/A_RELOAD_ALL/tools/enable_RESET.py",
    "BACKEND/B_RESET/A_run.py",
    # ##############################
    "BACKEND/D_FLOW/A_RELOAD_ALL/AAA_run_1_and_change_desktop_2.py",
    "BACKEND/D_FLOW/A_RELOAD_ALL/AAB_run_2_and_change_desktop_3.py",
    "BACKEND/D_FLOW/A_RELOAD_ALL/AAC_run_3_and_change_desktop_4.py",
    "BACKEND/D_FLOW/A_RELOAD_ALL/AAD_run_4_and_change_desktop_1.py",
]


def load_settings():
    """Читаем настройки из файла SETTINGS.py"""
    settings = {}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        exec(f.read(), settings)
    return settings


def load_yaml(path: str) -> dict:
    """Читаем YAML файл"""
    settings = {}
    with open(path, "r", encoding="utf-8") as f:
        exec(f.read(), settings)
    return settings


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
    """Одиночный запуск при совпадении значений"""
    settings = load_settings()
    config = load_yaml(CONFIG_FILE)

    val_main = settings.get(YAML_KEY_MAIN)
    val_conf = config.get(YAML_KEY_CONFIG)


    if val_main == val_conf:
        run_script_list(MAIN_SCRIPTS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
