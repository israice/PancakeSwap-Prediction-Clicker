
import ctypes
import time

user32 = ctypes.windll.user32

VK_LWIN = 0x5B
VK_CONTROL = 0x11
VK_D = 0x44

KEYEVENTF_KEYUP = 0x0002

def press_key(key):
    user32.keybd_event(key, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)

def create_desktop():
    user32.keybd_event(VK_LWIN, 0, 0, 0)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)

    press_key(VK_D)

    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

if __name__ == "__main__":
    create_desktop()
