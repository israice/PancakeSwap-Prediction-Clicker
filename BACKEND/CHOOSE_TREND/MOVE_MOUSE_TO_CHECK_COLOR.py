
import os
import re
import ctypes
from ctypes import wintypes

SETTINGS_FILE = "DASHBOARD.py"
VARIABLE_NAME = "MOVE_MOUSE_TO_CHECK_COLOR"

user32 = ctypes.WinDLL("user32", use_last_error=True)

try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)
    except Exception:
        user32.SetProcessDPIAware()


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


def main():
    path = SETTINGS_FILE

    if not os.path.isfile(path):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            SETTINGS_FILE
        )

    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(
                rf'^\s*{VARIABLE_NAME}\s*[:=]\s*["\']?(\d+)\s*,\s*(\d+)(?:\s*,\s*monitor=(\d+))?',
                line
            )
            if m:
                x, y = int(m.group(1)), int(m.group(2))
                monitor_id = int(m.group(3) or 1)
                break
        else:
            return

    monitors = []

    CALLBACK = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
        ctypes.POINTER(RECT), wintypes.LPARAM
    )

    def enum_callback(handle, dc, rect, data):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(info)
        if user32.GetMonitorInfoW(handle, ctypes.byref(info)):
            r = info.rcMonitor
            monitors.append((r.left, r.top, r.right - r.left, r.bottom - r.top,
                             bool(info.dwFlags & 1)))
        return True

    callback = CALLBACK(enum_callback)
    user32.EnumDisplayMonitors(None, None, callback, 0)

    monitors.sort(key=lambda m: not m[4])

    if 1 <= monitor_id <= len(monitors):
        mx, my, mw, mh, _ = monitors[monitor_id - 1]
        if 0 <= x < mw and 0 <= y < mh:
            user32.SetCursorPos(mx + x, my + y)


if __name__ == "__main__":
    main()
