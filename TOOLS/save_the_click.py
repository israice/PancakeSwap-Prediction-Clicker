# save_click.py
# Сохраняет ЛОКАЛЬНЫЕ координаты клика относительно монитора
# и номер монитора.
# Формат строки: test1 = "x,y,monitor=N"
# Не трогает прочие строки и их порядок.

import os
import sys
import platform
import ctypes
from ctypes import wintypes
from pynput import keyboard, mouse

from pynput.keyboard import Key

# ==============================
# Глобальные настройки
SETTINGS_FILE = "DASHBOARD.py"
VARIABLE_NAME = "TEST"
# ==============================


# ---- DPI awareness (важно для корректных координат на Windows) ----
def _make_dpi_aware():
    if platform.system() != "Windows":
        return

    try:
        user32 = ctypes.windll.user32

        # Попытка Per-Monitor v2
        try:
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            return
        except Exception:
            pass

        # Per-Monitor (Win 8.1+)
        try:
            shcore = ctypes.windll.shcore
            PROCESS_PER_MONITOR_DPI_AWARE = 2
            shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
            return
        except Exception:
            pass

        # System-DPI (fallback)
        user32.SetProcessDPIAware()

    except Exception:
        pass


# ---- WinAPI типы/функции ----
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


user32 = ctypes.windll.user32

user32.GetMonitorInfoW.argtypes = [
    wintypes.HMONITOR,
    ctypes.POINTER(MONITORINFO),
]
user32.GetMonitorInfoW.restype = wintypes.BOOL

MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(RECT),
    wintypes.LPARAM,
)

user32.EnumDisplayMonitors.argtypes = [
    wintypes.HDC,
    ctypes.c_void_p,
    MonitorEnumProc,
    wintypes.LPARAM,
]
user32.EnumDisplayMonitors.restype = wintypes.BOOL

MONITOR_DEFAULTTONEAREST = 2

user32.MonitorFromPoint.argtypes = [
    wintypes.POINT,
    wintypes.DWORD,
]
user32.MonitorFromPoint.restype = wintypes.HMONITOR


def _enum_monitors():
    monitors = []

    def _cb(hmon, hdc, lprc, lparam):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)

        if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            x = mi.rcMonitor.left
            y = mi.rcMonitor.top
            w = mi.rcMonitor.right - mi.rcMonitor.left
            h = mi.rcMonitor.bottom - mi.rcMonitor.top

            monitors.append({
                "handle": hmon,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            })

        return True

    cb = MonitorEnumProc(_cb)
    user32.EnumDisplayMonitors(0, None, cb, 0)

    return monitors


def _monitor_from_point(x, y):
    """Возвращает монитор, на котором находится точка (x, y)."""

    pt = wintypes.POINT(int(x), int(y))
    hmon = user32.MonitorFromPoint(
        pt, MONITOR_DEFAULTTONEAREST
    )

    mons = _enum_monitors()

    for i, monitor in enumerate(mons, start=1):
        if monitor["handle"] == hmon:
            monitor = monitor.copy()
            monitor["id"] = i
            return monitor

    if mons:
        monitor = mons[0].copy()
        monitor["id"] = 1
        return monitor

    return {
        "id": 1,
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0,
    }


# ---- Работа с файлом настроек ----
def _update_line_in_text(text, var_name, new_line):
    lines = text.splitlines(keepends=True)

    if not lines:
        return new_line

    updated = False

    for i, line in enumerate(lines):
        stripped = line.lstrip()

        if (
            stripped.startswith(f"{var_name} =")
            or stripped.startswith(f"{var_name}=")
        ):
            indent = line[:len(line) - len(stripped)]
            lines[i] = f"{indent}{new_line.rstrip()}\n"
            updated = True
            break

    if not updated:
        if not lines[-1].endswith("\n"):
            lines[-1] += "\n"

        lines.append(
            new_line if new_line.endswith("\n")
            else new_line + "\n"
        )

    return "".join(lines)


def _save_variable_line(var_name, x_local, y_local, monitor_id):
    # Формируем строковое значение в двойных кавычках.
    value = f"{x_local},{y_local},monitor={monitor_id}"
    new_value_line = f'{var_name} = "{value}"\n'

    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(new_value_line)

        print(f'{var_name} сохранён: "{value}"')
        return

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        original = f.read()

    updated_text = _update_line_in_text(
        original,
        var_name,
        new_value_line,
    )

    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        f.write(updated_text)

    print(f'{var_name} сохранён: "{value}"')


# ---- Разблокировка по нажатию обоих шифтов ----
class _ShiftGate:
    """Сохранение клика разрешено только после того, как пользователь
    одновременно зажал ЛЕВЫЙ и ПРАВЫЙ Shift."""

    def __init__(self):
        self.left = False
        self.right = False
        self.armed = False

    def _update(self):
        if not self.armed and self.left and self.right:
            self.armed = True
            print("Оба Shift нажаты — сохранение клика разрешено.")

    def on_press(self, key):
        if key == Key.shift:
            self.left = True
        elif key == Key.shift_r:
            self.right = True
        else:
            return

        self._update()

    def on_release(self, key):
        if key == Key.shift:
            self.left = False
        elif key == Key.shift_r:
            self.right = False


# ---- Обработка клика мыши ----
def _on_click(gate, var_name, x, y, button, pressed, *_):
    if not pressed:
        return

    if not gate.armed:
        print("Клик проигнорирован: сначала зажми оба Shift (левый и правый).")
        return

    monitor = _monitor_from_point(x, y)

    x_local = int(x - monitor["x"])
    y_local = int(y - monitor["y"])

    _save_variable_line(
        var_name,
        x_local,
        y_local,
        monitor["id"],
    )

    return False  # Один клик — и выходим


def main():
    if platform.system() != "Windows":
        raise OSError(
            "Этот скрипт использует Windows API и предназначен для Windows."
        )

    _make_dpi_aware()

    var_name = VARIABLE_NAME

    if len(sys.argv) >= 2 and sys.argv[1].strip():
        var_name = sys.argv[1].strip()

    gate = _ShiftGate()

    print("Зажми одновременно ЛЕВЫЙ и ПРАВЫЙ Shift, потом сделай клик.")

    with keyboard.Listener(
        on_press=gate.on_press,
        on_release=gate.on_release,
    ):
        with mouse.Listener(
            on_click=lambda *args: _on_click(gate, var_name, *args)
        ) as listener:
            listener.join()


if __name__ == "__main__":
    main()