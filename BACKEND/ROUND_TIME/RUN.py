import importlib.util
import os
import subprocess
import sys
from types import ModuleType

# --- Не создавать папки __pycache__ (bytecode-кэш) ---
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# ================= НАСТРОЙКИ =================
# SETTINGS.py — это обычный Python-файл (KEY = "value"), поэтому грузим его
# как модуль, а НЕ через yaml. Все пути — от корня проекта, с прямыми слешами
# (как в MAIN_SCRIPTS и во всех остальных скриптах проекта).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # корень проекта

SETTINGS_FILE = "DASHBOARD.py"
YAML_KEY_RUNNER = "ROUND_TIME"
RUNNER_ON_VALUE = "True"

MAIN_SCRIPTS = [
    {"print": "я тестовое сообщение..."},
    "BACKEND/ROUND_TIME/get_TIME_LEFT.py",
    "BACKEND/ROUND_TIME/plus_1m_to_TIME_LEFT.py",
    "BACKEND/ROUND_TIME/TIME_LEFT_BACK_COUNTER.py",
]
# ==============================================

# Консоль Windows по умолчанию cp1252/cp866 -> принудительно UTF-8,
# иначе русский текст вызовет UnicodeEncodeError.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if callable(_reconfigure):
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except OSError:
            pass


def load_settings() -> ModuleType:
    """Загружаем SETTINGS.py как Python-модуль.

    Явный spec_from_file_location, а не `import SETTINGS`: в проекте несколько
    файлов с именем SETTINGS.py, обычный импорт может подхватить чужой.
    """
    # Путь с прямыми слешами (как в MAIN_SCRIPTS) -> реальный путь на диске
    abs_settings = os.path.join(PROJECT_ROOT, SETTINGS_FILE.replace("/", os.sep))
    if not os.path.isfile(abs_settings):
        raise FileNotFoundError(f"Файл настроек не найден: {abs_settings}")

    spec = importlib.util.spec_from_file_location("b_open_the_website_settings", abs_settings)
    if spec is None or spec.loader is None:
        raise ImportError(f"Не удалось загрузить файл настроек: {abs_settings}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        # Пути в MAIN_SCRIPTS указаны от корня проекта, а скрипт может быть
        # запущен из любой папки -> работаем в PROJECT_ROOT.
        abs_script = os.path.join(PROJECT_ROOT, script.replace("/", os.sep))
        if not os.path.isfile(abs_script):
            print(f"[ERR] Файл не найден: {abs_script}")
            return
        subprocess.run([sys.executable, abs_script], check=False, cwd=PROJECT_ROOT)
    else:
        print(f"[WARN] Неверный тип шага: {script}")


def run_script_list(scripts):
    """Выполняем список шагов по очереди"""
    for i, script in enumerate(scripts, start=1):
        run_script(script)


def main():
    """Одиночный запуск"""
    settings = load_settings()
    if is_runner_on(getattr(settings, YAML_KEY_RUNNER, "")):
        run_script_list(MAIN_SCRIPTS)
    else:
        print(f"[SKIP] {YAML_KEY_RUNNER} выключен в SETTINGS.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
