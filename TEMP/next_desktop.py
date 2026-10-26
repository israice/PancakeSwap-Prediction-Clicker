import ctypes
import time

user32 = ctypes.windll.user32

VK_LWIN = 0x5B
VK_LCONTROL = 0xA2
VK_RIGHT = 0x27
VK_LEFT = 0x25

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002

def hotkey_combination(*keys):
    """Эмуляция комбинации клавиш"""
    for k in keys:
        user32.keybd_event(k, 0, KEYEVENTF_KEYDOWN, 0)
        time.sleep(0.03)
    for k in reversed(keys):
        user32.keybd_event(k, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.01)

def get_foreground_hwnd():
    return user32.GetForegroundWindow()

def switch_next_desktop():
    """
    Переход на следующий рабочий стол:
    - если следующий есть → обычный шаг вправо
    - если следующего нет → сразу на нулевой рабочий стол
    """
    hwnd_before = get_foreground_hwnd()

    # Пробуем один шаг вправо
    hotkey_combination(VK_LWIN, VK_LCONTROL, VK_RIGHT)
    time.sleep(0.25)

    hwnd_after = get_foreground_hwnd()

    if hwnd_after != hwnd_before:
        return

    # Если HWND не изменилось → был последний стол → wrap на первый
    print("Был последний стол → прыгаем на первый (нулевой)")
    # 10 шагов влево гарантируют попадание на первый
    for _ in range(10):
        hotkey_combination(VK_LWIN, VK_LCONTROL, VK_LEFT)
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Рекомендуется запускать скрипт от имени администратора.")
    except Exception:
        pass

    switch_next_desktop()
