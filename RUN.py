import subprocess
import sys
import os
import signal
from pathlib import Path

# Не создавать __pycache__
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

BASE_DIR = Path(__file__).resolve().parent

startup_scripts = [
    "BACKEND/ROUND_TIME/get_TIME_LEFT.py",
    "TOOLS/CONFIGS/disable_COLLECT_WINNINGS.py",
    "TOOLS/CONFIGS/disable_GO_LONG.py",
    "TOOLS/CONFIGS/disable_GO_SHORT.py",
]

loop_scripts = [
    {"print": "я multi desktop..."},
    "Z_TEST/A_run.py",
]

shutdown_scripts = [
    "TOOLS/CONFIGS/enable_COLLECT_WINNINGS.py",
    "TOOLS/CONFIGS/enable_GO_LONG.py",
    "TOOLS/CONFIGS/enable_GO_SHORT.py",
]

stop_requested = False
finish_current_list = False
force_stop = False
current_process = None
ctrl_c_count = 0


def handle_sigint(signum, frame):
    global ctrl_c_count, finish_current_list
    global stop_requested, force_stop

    ctrl_c_count += 1

    if ctrl_c_count == 1:
        finish_current_list = True
        print("\n⏹ Остановка после текущего списка.", flush=True)
    else:
        force_stop = True
        stop_requested = True
        print("\n🛑 Принудительная остановка.", flush=True)

        if current_process is not None:
            try:
                if current_process.poll() is None:
                    current_process.kill()
            except Exception:
                pass


signal.signal(signal.SIGINT, handle_sigint)


def run_script(script_path):
    global current_process, force_stop

    if force_stop:
        return

    # Записи-сообщения вида {"print": "текст"} просто выводятся и пропускаются
    if isinstance(script_path, dict):
        message = script_path.get("print")
        if message:
            print(message, flush=True)
        return

    # Универсально принимаем и строки, и объекты Path
    if isinstance(script_path, Path):
        script_path = str(script_path)

    path = BASE_DIR / Path(script_path)

    if not path.is_file():
        print(f"❌ Файл не найден: {path}", flush=True)
        return

    try:
        current_process = subprocess.Popen(
            [sys.executable, str(path)],
            cwd=str(BASE_DIR),
        )

        while True:
            if force_stop:
                if current_process.poll() is None:
                    current_process.kill()

                current_process.wait()
                current_process = None
                return

            try:
                return_code = current_process.wait(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                continue

        current_process = None

        if return_code != 0:
            print(f"⚠️ Скрипт завершился с кодом {return_code}: {script_path}", flush=True)

    except Exception as error:
        current_process = None
        print(f"❌ Ошибка {script_path}: {error}", flush=True)


def stop_current_process():
    global current_process

    if current_process is not None:
        try:
            if current_process.poll() is None:
                current_process.kill()
                current_process.wait()
        except Exception:
            pass

        current_process = None


def run_list(scripts, list_name):
    global stop_requested, finish_current_list

    for script in scripts:
        if force_stop:
            return

        run_script(script)

        if force_stop:
            return

    if finish_current_list:
        stop_requested = True
        finish_current_list = False


def main():
    global stop_requested

    try:
        run_list(startup_scripts, "STARTUP")

        while not stop_requested and not force_stop:
            run_list(loop_scripts, "LOOP")

    finally:
        if force_stop:
            stop_current_process()
            print("🛑 Программа остановлена. SHUTDOWN пропущен.", flush=True)
            return

        stop_requested = True
        stop_current_process()

        for script in shutdown_scripts:
            if force_stop:
                stop_current_process()
                return

            run_script(script)

        print("🏁 Runner завершён.", flush=True)


if __name__ == "__main__":
    main()