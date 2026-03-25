import sys
import time
import platform
import ctypes
import re
import codecs
from ctypes import wintypes
from pynput.mouse import Controller

# ==============================
SETTINGS_FILE = "SETTINGS.py"         # путь к файлу настроек
VAR_COORDS   = "CLICK_CANDLE_COLOR"     # имя переменной с координатами
VAR_RESULT   = "CANDLE_COLOR"           # ключ, куда записываем результат

VALUE_GREEN_WORD = "GREEN"
VALUE_RED_WORD   = "RED"
VALUE_ZERO_WORD  = "ZERO"               # <-- записываем это, если ни один цвет не совпал

COLOR_GREEN_HEX = "#31d0aa"
COLOR_RED_HEX   = "#ed4b9e"
COLOR_READ_DELAY = 0.5
# ==============================

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
            shcore.SetProcessDpiAwareness(2)
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
gdi32  = ctypes.windll.gdi32

user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
user32.GetMonitorInfoW.restype  = wintypes.BOOL

MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM
)
user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p, MonitorEnumProc, wintypes.LPARAM]
user32.EnumDisplayMonitors.restype  = wintypes.BOOL

gdi32.GetPixel.argtypes = [wintypes.HDC, wintypes.INT, wintypes.INT]
gdi32.GetPixel.restype  = wintypes.DWORD  # COLORREF

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype  = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype  = wintypes.INT

# ---- Мониторы ----
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

# ---- Парсинг строки "VAR: x,y,monitor=N" ----
def _parse_var_line(line, var_name):
    stripped = line.lstrip()
    if not (stripped.startswith(f"{var_name} =") or stripped.startswith(f"{var_name}=")):
        return None
    payload = stripped.split("=", 1)[1].strip()
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

def _load_coordinates(var_name, settings_path):
    with open(settings_path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8-sig", errors="replace")
    for raw_line in text.splitlines(keepends=False):
        parsed = _parse_var_line(raw_line, var_name)
        if parsed:
            return parsed
    raise ValueError(f"Переменная {var_name} не найдена в {settings_path}")

def _local_to_global(x_local, y_local, monitor_id, monitors):
    if not monitors:
        return x_local, y_local
    if monitor_id is not None and 1 <= monitor_id <= len(monitors):
        target = monitors[monitor_id - 1]
    else:
        target = monitors[0]
    gx = int(target["x"] + x_local)
    gy = int(target["y"] + y_local)
    return gx, gy

# ---- Цвет пикселя ----
def _get_pixel_hex(gx, gy):
    hdc = user32.GetDC(0)
    if not hdc:
        raise RuntimeError("GetDC вернул NULL")
    try:
        colorref = gdi32.GetPixel(hdc, gx, gy)
        if colorref == 0xFFFFFFFF:  # CLR_INVALID
            raise RuntimeError("GetPixel вернул CLR_INVALID")
        r = colorref & 0xFF
        g = (colorref >> 8) & 0xFF
        b = (colorref >> 16) & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    finally:
        user32.ReleaseDC(0, hdc)

# ---- Точная замена только значения у ключа ----
def _replace_yaml_scalar_value(settings_path, key, new_value):
    """
    Меняет только значение после 'key:' до комментария '#',
    сохраняя отступы, пробелы, комментарии, переводы строк и BOM.
    """
    with open(settings_path, "rb") as f:
        raw = f.read()

    had_bom = raw.startswith(codecs.BOM_UTF8)
    text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines(keepends=True)

    # новая регулярка с захватом конца строки
    pattern = re.compile(
        rf'^(\s*{re.escape(key)}\s*=\s*)([^#\r\n]*?)(\s*)((#.*)?)(\r?\n)?$',
        re.UNICODE
    )

    replaced = False
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            prefix = m.group(1)
            old_value = m.group(2)
            spacing = m.group(3)
            comment = m.group(4) or ""
            eol = m.group(6) or ""
            new_line = f"{prefix}{new_value}{spacing}{comment}{eol}"
            lines[i] = new_line
            replaced = True
            break

    if not replaced:
        raise ValueError(f"Ключ {key} не найден в {settings_path}")

    out_text = "".join(lines)
    out_bytes = out_text.encode("utf-8")
    if had_bom:
        out_bytes = codecs.BOM_UTF8 + out_bytes

    with open(settings_path, "wb") as f:
        f.write(out_bytes)

def main():
    _make_dpi_aware()

    # 1) читаем координаты
    x_local, y_local, monitor_id = _load_coordinates(VAR_COORDS, SETTINGS_FILE)
    monitors = _enum_monitors()
    gx, gy = _local_to_global(x_local, y_local, monitor_id, monitors)

    # 2) ставим курсор и ждём
    mouse = Controller()
    mouse.position = (gx, gy)
    time.sleep(COLOR_READ_DELAY)

    # 3) считываем цвет и 4) записываем слово
    hex_color = _get_pixel_hex(gx, gy)

    up = hex_color.upper()
    if up == COLOR_GREEN_HEX.upper():
        _replace_yaml_scalar_value(SETTINGS_FILE, VAR_RESULT, VALUE_GREEN_WORD)
    elif up == COLOR_RED_HEX.upper():
        _replace_yaml_scalar_value(SETTINGS_FILE, VAR_RESULT, VALUE_RED_WORD)
    else:
        # Если цвет не совпал ни с одним — записываем ZERO
        _replace_yaml_scalar_value(SETTINGS_FILE, VAR_RESULT, VALUE_ZERO_WORD)

if __name__ == "__main__":
    main()
