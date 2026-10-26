import subprocess
import os
import sys
import threading
from pathlib import Path
from pynput import keyboard

# --- Не создавать папки __pycache__ (bytecode-кэш) ---
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

UP_SCRIPT = "BACKEND/GO_LONG/RUN.py"
DOWN_SCRIPT = "BACKEND/GO_SHORT/RUN.py"
RIGHT_SCRIPT = "BACKEND/COLLECT_WINNINGS/RUN.py"

CTRL_KEYS = (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)

pressed_keys = set()
stop_event = threading.Event()


def launch_script(script_path):
    path = Path(script_path)

    if not path.is_file():
        print(f"\nФайл не найден: {script_path}")
        print(f"Текущая директория: {Path.cwd()}")
        return

    try:
        subprocess.Popen([sys.executable, str(path)])
        print(f"\nЗапущен скрипт: {script_path}")
    except Exception as error:
        print(f"\nОшибка запуска: {error}")


def ctrl_is_pressed():
    return any(key in pressed_keys for key in CTRL_KEYS)


def on_press(key):
    if key in CTRL_KEYS:
        pressed_keys.add(key)
        return

    # Ctrl+C — остановка программы
    if ctrl_is_pressed() and key == keyboard.KeyCode.from_char("c"):
        print("\nПолучена команда остановки Ctrl+C.")
        stop_event.set()
        return False

    # Стрелки работают только вместе с зажатым Ctrl
    if not ctrl_is_pressed():
        return

    if key == keyboard.Key.up:
        print("\nCtrl+стрелка вверх — ордер вверх.")
        launch_script(UP_SCRIPT)

    elif key == keyboard.Key.down:
        print("\nCtrl+стрелка вниз — ордер вниз.")
        launch_script(DOWN_SCRIPT)

    elif key == keyboard.Key.right:
        print("\nCtrl+стрелка вправо — сбор выигрышей.")
        launch_script(RIGHT_SCRIPT)


def on_release(key):
    pressed_keys.discard(key)


def main():
    print("Keyboard Server запущен.")
    print("Для остановки нажми Ctrl+C или Ctrl+Break.")
    print("Ctrl+стрелка вверх = ордер вверх, Ctrl+стрелка вниз = ордер вниз, "
          "Ctrl+стрелка вправо = сбор выигрышей.")

    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )

    listener.start()

    try:
        while not stop_event.wait(0.2):
            if not listener.is_alive():
                break
    except KeyboardInterrupt:
        print("\nПолучен сигнал остановки.")
    finally:
        listener.stop()
        listener.join(timeout=2)
        print("Keyboard Server остановлен.")


if __name__ == "__main__":
    main()