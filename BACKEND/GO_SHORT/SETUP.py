# save_click.py
# Последовательно сохраняет локальные координаты кликов
# относительно монитора для списка констант.
#
# Формат:
# CLICK_ENTER_UP_BUTTON = "811,713,monitor=2"
#
# Shift + Shift нужны только один раз перед первым кликом.
# Остальные клики сохраняются без повторного нажатия Shift.

import os
import platform
import ctypes
from ctypes import wintypes

from pynput import keyboard, mouse
from pynput.keyboard import Key


# ==========================================
# ГЛОБАЛЬНЫЕ НАСТРОЙКИ
# ==========================================

SETTINGS_FILE = "DASHBOARD.py"

VARIABLES = [
    "CLICK_ENTER_DOWN_BUTTON",
    "CLICK_ON_TEXT_AREA",
    "CLICK_ON_CONFIRM_IN_WEBSITE",
    "CLICK_ON_CONFIRM_IN_METAMASK",
]

# ==========================================


# ---- DPI awareness ----
def _make_dpi_aware():
    if platform.system() != "Windows":
        return

    try:
        user32 = ctypes.windll.user32

        # Per-Monitor v2
        try:
            user32.SetProcessDpiAwarenessContext(
                ctypes.c_void_p(-4)
            )
            return
        except Exception:
            pass

        # Per-Monitor (Windows 8.1+)
        try:
            shcore = ctypes.windll.shcore
            PROCESS_PER_MONITOR_DPI_AWARE = 2

            shcore.SetProcessDpiAwareness(
                PROCESS_PER_MONITOR_DPI_AWARE
            )
            return
        except Exception:
            pass

        # System-DPI fallback
        user32.SetProcessDPIAware()

    except Exception:
        pass


# ---- WinAPI типы ----
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


# ---- Получение списка мониторов ----
def _enum_monitors():
    monitors = []

    def _cb(hmon, hdc, lprc, lparam):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)

        if user32.GetMonitorInfoW(
            hmon,
            ctypes.byref(mi),
        ):
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

    callback = MonitorEnumProc(_cb)

    user32.EnumDisplayMonitors(
        0,
        None,
        callback,
        0,
    )

    return monitors


# ---- Определение монитора по координатам ----
def _monitor_from_point(x, y):
    point = wintypes.POINT(int(x), int(y))

    handle = user32.MonitorFromPoint(
        point,
        MONITOR_DEFAULTTONEAREST,
    )

    monitors = _enum_monitors()

    for i, monitor in enumerate(monitors, start=1):
        if monitor["handle"] == handle:
            result = monitor.copy()
            result["id"] = i
            return result

    if monitors:
        result = monitors[0].copy()
        result["id"] = 1
        return result

    return {
        "id": 1,
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0,
    }


# ---- Обновление строки константы в файле ----
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

            # Сохраняем отсутствие завершающего перевода строки,
            # если обновляем последнюю строку файла.
            newline = "\n" if line.endswith("\n") else ""

            lines[i] = (
                f"{indent}{new_line.rstrip()}{newline}"
            )
            updated = True
            break

    # Если константа отсутствует, добавляем её в конец.
    if not updated:
        if not lines[-1].endswith("\n"):
            lines[-1] += "\n"

        lines.append(
            new_line
            if new_line.endswith("\n")
            else new_line + "\n"
        )

    return "".join(lines)


# ---- Сохранение координат одной константы ----
def _save_variable_line(
    var_name,
    x_local,
    y_local,
    monitor_id,
):
    value = f"{x_local},{y_local},monitor={monitor_id}"
    new_line = f'{var_name} = "{value}"\n'

    if not os.path.exists(SETTINGS_FILE):
        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            file.write(new_line)

        print(f'Сохранено: {var_name} = "{value}"')
        return

    with open(
        SETTINGS_FILE,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        original = file.read()

    updated_text = _update_line_in_text(
        original,
        var_name,
        new_line,
    )

    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        file.write(updated_text)

    print(f'Сохранено: {var_name} = "{value}"')


# ---- Разблокировка по нажатию обоих Shift ----
class _ShiftGate:
    def __init__(self):
        self.left = False
        self.right = False
        self.armed = False

    def _update(self):
        if (
            not self.armed
            and self.left
            and self.right
        ):
            self.armed = True

            print(
                "\nОба Shift нажаты — сохранение разрешено."
            )
            print(
                "Теперь делай все клики подряд. "
                "Повторно нажимать Shift не нужно.\n"
            )

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


# ---- Обработка последовательности кликов ----
class _ClickSequence:
    def __init__(self, variables):
        self.variables = variables
        self.index = 0
        self.gate = _ShiftGate()

    def on_click(self, x, y, button, pressed):
        if not pressed:
            return

        # Пока оба Shift не были зажаты одновременно,
        # клики игнорируются.
        if not self.gate.armed:
            print(
                "Клик проигнорирован: сначала одновременно "
                "зажми левый и правый Shift."
            )
            return

        if self.index >= len(self.variables):
            return False

        var_name = self.variables[self.index]

        monitor = _monitor_from_point(x, y)

        x_local = int(x - monitor["x"])
        y_local = int(y - monitor["y"])

        _save_variable_line(
            var_name,
            x_local,
            y_local,
            monitor["id"],
        )

        self.index += 1

        if self.index >= len(self.variables):
            print(
                "\nВсе координаты сохранены. "
                "Работа завершена."
            )
            return False

        next_var = self.variables[self.index]

        print(
            f"\nСохранено {self.index} "
            f"из {len(self.variables)}."
        )
        print(f"Следующая константа: {next_var}")
        print(
            "Делай следующий клик — "
            "Shift нажимать повторно не нужно."
        )

    def on_key_press(self, key):
        self.gate.on_press(key)

    def on_key_release(self, key):
        self.gate.on_release(key)


# ---- Запуск ----
def main():
    if platform.system() != "Windows":
        raise OSError(
            "Этот скрипт использует Windows API "
            "и предназначен для Windows."
        )

    if not VARIABLES:
        print("Список VARIABLES пуст.")
        return

    if len(set(VARIABLES)) != len(VARIABLES):
        raise ValueError(
            "В списке VARIABLES обнаружены повторяющиеся константы."
        )

    _make_dpi_aware()

    sequence = _ClickSequence(VARIABLES)

    print("=" * 50)
    print("ПОСЛЕДОВАТЕЛЬНОЕ СОХРАНЕНИЕ КООРДИНАТ")
    print("=" * 50)
    print(f"Файл: {SETTINGS_FILE}")
    print(f"Всего кликов: {len(VARIABLES)}")
    print()
    print(f"Первая константа: {VARIABLES[0]}")
    print(
        "Одновременно зажми левый и правый Shift "
        "только один раз."
    )
    print("Затем делай клики по очереди.")
    print()

    with keyboard.Listener(
        on_press=sequence.on_key_press,
        on_release=sequence.on_key_release,
    ):
        with mouse.Listener(
            on_click=sequence.on_click,
        ) as listener:
            listener.join()


if __name__ == "__main__":
    main()