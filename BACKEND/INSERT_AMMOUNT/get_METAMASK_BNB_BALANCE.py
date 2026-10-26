#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from decimal import Decimal, ROUND_HALF_UP
from web3 import Web3


# ============================================================
# НАСТРОЙКИ И ПУТИ
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

SETTINGS_PATH = os.path.join(PROJECT_ROOT, "DASHBOARD.py")
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

YAML_KEY = "WALLET_BALANCE"
ENV_ADDRESS_KEY = "METAMASK_BSC_ADDRESS"
ENV_RPC_KEY = None

RPC_URL = "https://bsc-dataseed1.bnbchain.org"
RPC_TIMEOUT = 10
DECIMAL_PLACES = 8


# ============================================================
# РЕГУЛЯРНОЕ ВЫРАЖЕНИЕ
# ============================================================

VALUE_PATTERN = re.compile(
    rf'^(\s*{re.escape(YAML_KEY)}\s*=\s*)'
    rf'(["\']?)([^\s#"\']+)(\2)(\s*(?:#.*)?)$',
    re.MULTILINE
)


# ============================================================
# ЧТЕНИЕ .ENV
# ============================================================

def read_env_var(path: str, key: str) -> str | None:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith(key + "="):
                value = line.split("=", 1)[1].strip()

                if (
                    len(value) >= 2
                    and value[0] == value[-1]
                    and value[0] in ("'", '"')
                ):
                    value = value[1:-1]

                return value

    return None


def require_env_address(path: str, key: str) -> str:
    try:
        address = read_env_var(path, key)
    except FileNotFoundError:
        raise SystemExit(f"Файл .env не найден: {path}")

    if not address:
        raise SystemExit(f"Не найден {key} в {path}")

    return address


# ============================================================
# ПОЛУЧЕНИЕ БАЛАНСА BNB
# ============================================================

def get_bnb_balance(addr: str, rpc_url: str) -> str:
    if not Web3.is_address(addr):
        raise SystemExit("Некорректный адрес кошелька")

    w3 = Web3(
        Web3.HTTPProvider(
            rpc_url,
            request_kwargs={"timeout": RPC_TIMEOUT}
        )
    )

    checksum_addr = Web3.to_checksum_address(addr)
    wei = w3.eth.get_balance(checksum_addr)

    balance = Decimal(wei) / Decimal(10**18)
    quantum = Decimal(1).scaleb(-DECIMAL_PLACES)

    balance = balance.quantize(
        quantum,
        rounding=ROUND_HALF_UP
    )

    return format(balance, "f")


# ============================================================
# ОБНОВЛЕНИЕ DASHBOARD.py
# ============================================================

def update_value(path: str, new_value: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise SystemExit(f"Файл настроек не найден: {path}")

    if not VALUE_PATTERN.search(text):
        raise SystemExit(
            f'Строка "{YAML_KEY} =" не найдена в {path}'
        )

    def replace_value(match):
        prefix, quote, _old_value, _closing_quote, tail = match.groups()
        return f"{prefix}{quote}{new_value}{quote}{tail}"

    new_text = VALUE_PATTERN.sub(
        replace_value,
        text,
        count=1
    )

    if new_text != text:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)


# ============================================================
# MAIN
# ============================================================

def main():
    addr = require_env_address(
        ENV_PATH,
        ENV_ADDRESS_KEY
    )

    rpc_url = RPC_URL

    if ENV_RPC_KEY:
        rpc_from_env = read_env_var(ENV_PATH, ENV_RPC_KEY)
        if rpc_from_env:
            rpc_url = rpc_from_env

    balance = get_bnb_balance(addr, rpc_url)

    update_value(SETTINGS_PATH, balance)


if __name__ == "__main__":
    main()