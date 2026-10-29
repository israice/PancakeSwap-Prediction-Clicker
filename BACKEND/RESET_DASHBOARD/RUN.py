import os
import sys

# --- Не создавать папки __pycache__ (bytecode-кэш) ---
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import subprocess
import sys

# ================= НАСТРОЙКИ =================
# Пути — от корня проекта, с прямыми слешами (как во всех скриптах проекта)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # корень проекта

MAIN_SCRIPTS: list[str | dict[str, str]] = [
    {"print": "я тестовое сообщение..."},
    "BACKEND/RESET_DASHBOARD/create_AMOUNT_IN_BNB.py",
    "BACKEND/RESET_DASHBOARD/reset_ALL_ROUNDS_COUNTER.py",
    "BACKEND/INSERT_AMOUNT/get_METAMASK_BNB_BALANCE.py",
]
# ==============================================


def main() -> None:
    for script in MAIN_SCRIPTS:
        if isinstance(script, dict):
            message = script.get("print")
            if message is not None:
                print(message, flush=True)
            continue

        script_path: str = script

        # Путь с прямыми слешами (как во всём проекте) -> реальный путь на диске
        abs_script = os.path.join(PROJECT_ROOT, script_path.replace("/", os.sep))
        if not os.path.isfile(abs_script):
            print(f"[ERR] Файл не найден: {abs_script}", flush=True)
            continue

        print(f"\n=== RUN {abs_script} ===", flush=True)

        result = subprocess.run(
            [sys.executable, abs_script],
            check=False,
            cwd=PROJECT_ROOT,
        )

        print(f"=== EXIT CODE: {result.returncode} ===", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
