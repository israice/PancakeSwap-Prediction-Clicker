#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from decimal import Decimal, getcontext
from web3 import Web3

# ===== НАСТРОЙКИ =====
SETTINGS_PATH = "SETTINGS.py"
YAML_KEY = "END_BNB_METAMASK_BALANCE"

ENV_PATH = ".env"
ENV_ADDRESS_KEY = "METAMASK_BSC_ADDRESS"   # имя переменной с адресом
ENV_RPC_KEY = None  # например, "BSC_RPC_URL"; None — не читать RPC из .env
RPC_URL = "https://bsc-dataseed1.bnbchain.org"  # BSC Mainnet (дефолт; может быть переопределён через ENV_RPC_KEY)
DECIMAL_PLACES = 8  # сколько знаков писать в YAML

getcontext().prec = 80  # высокая точность для деления wei -> BNB

def read_env_var(path: str, key: str) -> str | None:
    """Прочитать значение key= из .env (строгое совпадение префикса), вернуть None если не найдено."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith(key + "="):
                val = s.split("=", 1)[1].strip()
                # снять возможные кавычки
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                return val
    return None

def require_env_address(path: str, key: str) -> str:
    val = read_env_var(path, key)
    if not val:
        raise SystemExit(f"Не найден {key} в {path}")
    return val

def get_bnb_balance(addr: str, rpc_url: str) -> Decimal:
    if not Web3.is_address(addr):
        raise SystemExit("Некорректный адрес (ожидается 0x...)")
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
    addr = Web3.to_checksum_address(addr)
    wei = w3.eth.get_balance(addr)
    return Decimal(wei) / Decimal(10**18)

def update_yaml_value(path: str, new_value: str, key: str = YAML_KEY) -> None:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # сохраняем отступы, кавычки (если были), и хвост (пробелы/комментарий)
    pattern = re.compile(
        rf'^(\s*{re.escape(key)}\s*=\s*)(["\']?)([^\s#"\']+)(\2)(\s*(?:#.*)?)$',
        re.MULTILINE
    )
    if not pattern.search(text):
        raise SystemExit(f'Строка "{key} =" не найдена в {path}')

    def repl(m):
        prefix, q1, _old, q2, tail = m.groups()
        return f"{prefix}{q1}{new_value}{q2}{tail}"

    new_text = pattern.sub(repl, text, count=1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)

def main():
    # адрес из .env по ключу ENV_ADDRESS_KEY
    addr = require_env_address(ENV_PATH, ENV_ADDRESS_KEY)

    # RPC: либо из .env по ENV_RPC_KEY (если задан и найден), либо дефолтный RPC_URL
    rpc_url = RPC_URL
    if ENV_RPC_KEY:
        rpc_from_env = read_env_var(ENV_PATH, ENV_RPC_KEY)
        if rpc_from_env:
            rpc_url = rpc_from_env

    bal = get_bnb_balance(addr, rpc_url)

    # формат строго с DECIMAL_PLACES знаков (без экспоненты)
    bal_str = format(bal.quantize(Decimal(10) ** -DECIMAL_PLACES), "f")
    update_yaml_value(SETTINGS_PATH, bal_str, YAML_KEY)

if __name__ == "__main__":
    main()
