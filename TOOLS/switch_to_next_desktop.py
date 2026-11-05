
"""
Переключение на следующий виртуальный рабочий стол с зацикливанием:
с последнего стола переход на первый (Win+Ctrl+-> сам по себе этого не умеет).

Работает через COM-интерфейс Windows (обёртка pyvda), поэтому переключение
мгновенное и не зависит от раскладки/фокуса окна.

Требования: pip install pyvda
"""

import sys

# Кириллица в консоли Windows (cp1252) -> принудительно UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from pyvda import VirtualDesktop, get_virtual_desktops
except ImportError:
    print("Нужна библиотека pyvda:  pip install pyvda")
    sys.exit(1)


def next_desktop():
    desktops = get_virtual_desktops()
    if not desktops:
        print("Не удалось получить список рабочих столов.")
        return

    current = VirtualDesktop.current()

    # Ищем текущий стол в списке и переходим на следующий по кругу
    next_desktop_obj = None
    for i, d in enumerate(desktops):
        if d.number == current.number:
            next_desktop_obj = desktops[(i + 1) % len(desktops)]
            break

    if next_desktop_obj is None:
        # Текущий стол не найден в списке (бывает на пограничных версиях Windows)
        next_desktop_obj = desktops[0]

    next_desktop_obj.go()
    print(f"Стол {current.number} -> {next_desktop_obj.number}")


if __name__ == "__main__":
    next_desktop()
