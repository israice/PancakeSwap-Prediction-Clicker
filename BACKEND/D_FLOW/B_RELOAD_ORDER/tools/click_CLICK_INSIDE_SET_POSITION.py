# click_point.py
# Читает: CLICK_INSIDE_SET_POSITION: x,y,monitor=N из SETTINGS.py
# Конвертирует локальные координаты монитора в глобальные и делает левый клик.
# После клика вставляет через Ctrl+V значение INSERT_AMMOUNT из SETTINGS.py.

import sys
import time
import platform
import ctypes
from ctypes import wintypes
from pynput.mouse import Controller, Button

# ==============================
SETTINGS_FILE = "SETTINGS.py"                    # путь к файлу настроек
VARIABLE_NAME = "CLICK_INSIDE_SET_POSITION"        # имя переменной координат (можно переопределить аргументом)
CLICK_DELAY = 0.5                                  # задержка перед/после клика, сек
INSERT_VAR_NAME = "INSERT_AMMOUNT_IN_BNB"                 # имя переменной со значением для вставки
# ==============================

mouse = Controller()

# ---- DPI awareness ----
def _make_dpi_aware():
    if platform.system() != "Windows":
        return
    try:
        u32 = ctypes.windll.user32
        try:
            # PER_MONITOR_AWARE_V2
            u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
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
        u32.SetProcessDPIAware()
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
kernel32 = ctypes.windll.kernel32

# EnumDisplayMonitors / GetMonitorInfo
user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
user32.GetMonitorInfoW.restype = wintypes.BOOL
MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM
)
user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p, MonitorEnumProc, wintypes.LPARAM]
user32.EnumDisplayMonitors.restype = wintypes.BOOL

# --- сигнатуры для работы с буфером обмена/памятью ---
HGLOBAL = wintypes.HANDLE  # алиас

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype  = HGLOBAL
kernel32.GlobalLock.argtypes  = [HGLOBAL]
kernel32.GlobalLock.restype   = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [HGLOBAL]
kernel32.GlobalUnlock.restype  = wintypes.BOOL
kernel32.GlobalFree.argtypes   = [HGLOBAL]
kernel32.GlobalFree.restype    = HGLOBAL

user32.OpenClipboard.argtypes  = [wintypes.HWND]
user32.OpenClipboard.restype   = wintypes.BOOL
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype  = wintypes.BOOL
user32.SetClipboardData.argtypes = [wintypes.UINT, HGLOBAL]
user32.SetClipboardData.restype  = HGLOBAL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype  = wintypes.BOOL

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
    if monitors:
        if monitor_id is not None and 1 <= monitor_id <= len(monitors):
            target = monitors[monitor_id - 1]
        else:
            target = monitors[0]
        gx = int(target["x"] + x_local)
        gy = int(target["y"] + y_local)
    else:
        gx, gy = x_local, y_local
    return gx, gy

# ---- Загрузка скалярного значения из SETTINGS.py ----
def _load_scalar(var_name):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(f"{var_name} =") or line.startswith(f"{var_name}="):
                val = line.split("=", 1)[1].strip()
                # убираем возможные кавычки
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                # обрезаем возможный комментарий в конце строки
                if "#" in val:
                    val = val.split("#", 1)[0].strip()
                return val
    raise ValueError(f"Переменная {var_name} не найдена в {SETTINGS_FILE}")

# ---- Копирование текста в буфер обмена Windows ----
def _set_clipboard_text(text: str):
    if platform.system() != "Windows":
        return  # Ожидается Windows
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    if not user32.OpenClipboard(None):
        raise RuntimeError("Не удалось открыть буфер обмена")
    try:
        if not user32.EmptyClipboard():
            raise RuntimeError("Не удалось очистить буфер обмена")

        # Готовим UTF-16 строку + нуль-терминатор
        data = ctypes.create_unicode_buffer(text)
        size_bytes = (len(text) + 1) * ctypes.sizeof(ctypes.c_wchar)

        # Выделяем и заполняем глобальную память
        h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, size_bytes)
        if not h_global:
            raise RuntimeError("GlobalAlloc вернул NULL")

        lp_global = kernel32.GlobalLock(h_global)
        if not lp_global:
            kernel32.GlobalFree(h_global)
            raise RuntimeError("GlobalLock вернул NULL")

        try:
            ctypes.memmove(lp_global, ctypes.addressof(data), size_bytes)
        finally:
            kernel32.GlobalUnlock(h_global)

        # Передаём владение системе; при успехе память не освобождаем вручную
        if not user32.SetClipboardData(CF_UNICODETEXT, h_global):
            kernel32.GlobalFree(h_global)
            raise RuntimeError("SetClipboardData не удалось")
    finally:
        user32.CloseClipboard()

# ---- Надёжная вставка Ctrl+V через keybd_event (без конфликтов с pynput) ----
VK_CONTROL = 0x11
VK_V       = 0x56
KEYEVENTF_KEYUP = 0x0002

def _keybd_event(vk, flags=0):
    # Не задаём argtypes для keybd_event, чтобы не конфликтовать с другими библиотеками
    user32.keybd_event(vk, 0, flags, 0)

def _paste_ctrl_v():
    _keybd_event(VK_CONTROL, 0)           # Ctrl down
    _keybd_event(VK_V, 0)                 # V down
    _keybd_event(VK_V, KEYEVENTF_KEYUP)   # V up
    _keybd_event(VK_CONTROL, KEYEVENTF_KEYUP)  # Ctrl up

def main():
    _make_dpi_aware()

    # Имя переменной координат можно переопределить первым аргументом
    var_name = VARIABLE_NAME
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        var_name = sys.argv[1].strip()

    # 1) Координаты клика
    x_local, y_local, monitor_id = _load_coordinates(var_name)
    monitors = _enum_monitors()
    gx, gy = _local_to_global(x_local, y_local, monitor_id, monitors)

    # 2) Копируем значение в буфер обмена (до клика)
    insert_value = _load_scalar(INSERT_VAR_NAME)
    _set_clipboard_text(str(insert_value))

    # 3) Перемещаем курсор и кликаем
    mouse.position = (gx, gy)
    time.sleep(CLICK_DELAY)               # задержка перед кликом
    mouse.click(Button.left, 1)

    # 4) Вставляем через Ctrl+V после клика
    time.sleep(CLICK_DELAY)               # задержка после клика
    _paste_ctrl_v()

if __name__ == "__main__":
    main()
