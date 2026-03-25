# save_click.py
# Сохраняет ЛОКАЛЬНЫЕ координаты клика относительно монитора + номер монитора.
# Формат строки: PIXEL_POINT: x,y,monitor=N
# Не трогает прочие строки и их порядок.

import os
import sys
import platform
import ctypes
from ctypes import wintypes
from pynput import mouse

# ==============================
# Глобальные настройки
SETTINGS_FILE = "SETTINGS.py"     # путь к файлу настроек
VARIABLE_NAME = "PIXEL_CONFIG"       # имя переменной по умолчанию (можно переопределить аргументом)
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
    _fields_ = [("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG)]

class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD)]

user32 = ctypes.windll.user32
user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
user32.GetMonitorInfoW.restype = wintypes.BOOL

MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM
)
user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p, MonitorEnumProc, wintypes.LPARAM]
user32.EnumDisplayMonitors.restype = wintypes.BOOL

MONITOR_DEFAULTTONEAREST = 2
user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
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
            monitors.append({"handle": hmon, "x": x, "y": y, "w": w, "h": h})
        return True

    cb = MonitorEnumProc(_cb)   # держим ссылку!
    user32.EnumDisplayMonitors(0, None, cb, 0)
    return monitors

def _monitor_from_point(x, y):
    """Возвращает словарь монитора по глобальной точке (x, y)."""
    pt = wintypes.POINT(int(x), int(y))  # <-- используем wintypes.POINT
    hmon = user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
    mons = _enum_monitors()
    for i, m in enumerate(mons, start=1):
        if m["handle"] == hmon:
            m = m.copy()
            m["id"] = i
            return m
    if mons:
        m0 = mons[0].copy()
        m0["id"] = 1
        return m0
    return {"id": 1, "x": 0, "y": 0, "w": 0, "h": 0}

# ---- Работа с файлом настроек ----
def _update_line_in_text(text, var_name, new_line):
    lines = text.splitlines(keepends=True)
    if not lines:
        return new_line

    updated = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(f"{var_name} =") or stripped.startswith(f"{var_name}="):
            indent = line[: len(line) - len(stripped)]
            nl = "\n" if line.endswith("\n") else "\n"
            lines[i] = f"{indent}{new_line.rstrip()}{nl}"
            updated = True
            break

    if not updated:
        if not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(new_line if new_line.endswith("\n") else new_line + "\n")

    return "".join(lines)

def _save_variable_line(var_name, x_local, y_local, monitor_id):
    new_value_line = f"{var_name} = {x_local},{y_local},monitor={monitor_id}\n"
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(new_value_line)
        print(f"{var_name} сохранён: {x_local},{y_local},monitor={monitor_id}")
        return

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        original = f.read()
    updated_text = _update_line_in_text(original, var_name, new_value_line)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        f.write(updated_text)

# Принимаем «лишние» аргументы от pynput (на Windows есть injected)
def _on_click(var_name, x, y, button, pressed, *_):
    if not pressed:
        return
    mon = _monitor_from_point(x, y)
    x_local = int(x - mon["x"])
    y_local = int(y - mon["y"])
    _save_variable_line(var_name, x_local, y_local, mon["id"])
    return False  # один клик — и выходим

def main():
    _make_dpi_aware()
    var_name = VARIABLE_NAME
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        var_name = sys.argv[1].strip()

    with mouse.Listener(on_click=lambda *args: _on_click(var_name, *args)) as listener:
        listener.join()

if __name__ == "__main__":
    main()
