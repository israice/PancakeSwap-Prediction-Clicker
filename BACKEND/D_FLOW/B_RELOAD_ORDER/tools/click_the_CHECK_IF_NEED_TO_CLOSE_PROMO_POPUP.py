# click_point.py
# Читает: PIXEL_POINT: x,y,monitor=N
# Конвертирует локальные координаты монитора в глобальные и делает левый клик.

import sys
import time
import platform
import ctypes
from ctypes import wintypes
from pynput.mouse import Controller, Button

# ==============================
SETTINGS_FILE = "SETTINGS.py"     # путь к файлу настроек
VARIABLE_NAME = "CHECK_IF_NEED_TO_CLOSE_PROMO_POPUP"       # имя переменной по умолчанию (можно переопределить аргументом)
CLICK_DELAY = 0.5                  # задержка перед кликом, сек
# ==============================

mouse = Controller()

# ---- DPI awareness ----
def _make_dpi_aware():
    if platform.system() != "Windows":
        return
    try:
        user32 = ctypes.windll.user32
        try:
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            return
        except Exception:
            pass
        try:
            shcore = ctypes.windll.shcore
            PROCESS_PER_MONITOR_DPI_AWARE = 2
            shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
            return
        except Exception:
            pass
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

    cb = MonitorEnumProc(_cb)  # держим ссылку!
    user32.EnumDisplayMonitors(0, None, cb, 0)
    return monitors

# ---- Парсинг SETTINGS.py ----
def _parse_var_line(line, var_name):
    stripped = line.lstrip()
    if not (stripped.startswith(f"{var_name} =") or stripped.startswith(f"{var_name}=")):
        return None
    payload = stripped.split("=", 1)[1].strip()  # "x,y,monitor=N"
    parts = [p.strip() for p in payload.split(",")]
    if len(parts) < 2:
        return None
    try:
        x_local = int(parts[0])
        y_local = int(parts[1])
    except ValueError:
        return None

    monitor_id = None
    for p in parts[2:]:
        if p.startswith("monitor="):
            try:
                monitor_id = int(p.split("=", 1)[1])
            except ValueError:
                pass
    return x_local, y_local, monitor_id

def _load_coordinates(var_name):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            parsed = _parse_var_line(raw, var_name)
            if parsed:
                return parsed
    raise ValueError(f"Переменная {var_name} не найдена в {SETTINGS_FILE}")

def _local_to_global(x_local, y_local, monitor_id, monitors):
    # monitor_id нумеруем с 1 (в порядке EnumDisplayMonitors)
    target = None
    if monitor_id is not None and 1 <= monitor_id <= len(monitors):
        target = monitors[monitor_id - 1]
    else:
        target = monitors[0] if monitors else {"x": 0, "y": 0}

    gx = int(target["x"] + x_local)
    gy = int(target["y"] + y_local)
    return gx, gy

def main():
    _make_dpi_aware()
    var_name = VARIABLE_NAME
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        var_name = sys.argv[1].strip()

    x_local, y_local, monitor_id = _load_coordinates(var_name)
    monitors = _enum_monitors()
    gx, gy = _local_to_global(x_local, y_local, monitor_id, monitors)

    mouse.position = (gx, gy)
    time.sleep(CLICK_DELAY)
    mouse.click(Button.left, 1)

if __name__ == "__main__":
    main()
