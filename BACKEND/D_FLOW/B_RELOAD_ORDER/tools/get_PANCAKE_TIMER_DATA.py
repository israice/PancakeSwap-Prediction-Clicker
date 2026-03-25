# -*- coding: utf-8 -*-

import os
import re
import time
from pathlib import Path
from typing import List, Tuple

from web3 import Web3, HTTPProvider
from web3.exceptions import ContractLogicError

# =========================
# НАСТРОЙКИ
# =========================
SETTINGS_PATH = "SETTINGS.py"   # только прямые слэши
KEY_NAME      = "CANDLE_TIME"
CONTRACT_ADDR = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"  # Prediction V2 (BNB)
RPC_TIMEOUT_S = 8
RPC_URLS: List[str] = [
    os.getenv("BSC_RPC_URL", "").strip(),        # приоритет — ваш собственный RPC (если задан)
    "https://bsc-dataseed.bnbchain.org",
    "https://rpc.ankr.com/bsc",
    "https://bsc-rpc.publicnode.com",
    "https://1rpc.io/bnb",
]
RPC_URLS = [u for u in RPC_URLS if u]

# Точный минимальный ABI (ВАЖЕН порядок полей в rounds)
PREDICTION_ABI = [
    {
        "inputs": [],
        "name": "currentEpoch",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "rounds",
        "outputs": [
            {"internalType": "uint256", "name": "epoch", "type": "uint256"},
            {"internalType": "uint256", "name": "startTimestamp", "type": "uint256"},
            {"internalType": "uint256", "name": "lockTimestamp", "type": "uint256"},
            {"internalType": "uint256", "name": "closeTimestamp", "type": "uint256"},
            {"internalType": "int256",  "name": "lockPrice", "type": "int256"},
            {"internalType": "int256",  "name": "closePrice", "type": "int256"},
            {"internalType": "uint256", "name": "lockOracleId", "type": "uint256"},
            {"internalType": "uint256", "name": "closeOracleId", "type": "uint256"},
            {"internalType": "uint256", "name": "totalAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "bullAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "bearAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "rewardBaseCalAmount", "type": "uint256"},
            {"internalType": "uint256", "name": "rewardAmount", "type": "uint256"},
            {"internalType": "bool",    "name": "oracleCalled", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# ---------- RPC ----------
def get_web3_or_raise() -> Web3:
    errs = []
    for url in RPC_URLS:
        try:
            w3 = Web3(HTTPProvider(url, request_kwargs={"timeout": RPC_TIMEOUT_S}))
            if w3.is_connected() and int(w3.eth.chain_id) == 56:
                return w3
            errs.append(f"{url} (not connected or wrong chain)")
        except Exception as e:
            errs.append(f"{url} ({e})")
    raise RuntimeError("RPC недоступны:\n" + "\n".join(errs))

# ---------- Таймер ----------
def fetch_lock_close(w3: Web3) -> Tuple[int, int]:
    c = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=PREDICTION_ABI)
    try:
        epoch = c.functions.currentEpoch().call()
        rd = c.functions.rounds(epoch).call()
    except (ContractLogicError, Exception) as e:
        raise RuntimeError(f"Ошибка вызова контракта: {e}")
    lock_ts  = int(rd[2])
    close_ts = int(rd[3])
    return lock_ts, close_ts

def to_mmss(lock_ts: int, close_ts: int) -> str:
    now = int(time.time())
    remain = (lock_ts - now) if now < lock_ts else (close_ts - now)
    if remain < 0:
        remain = 0
    if remain > 300:
        remain %= 300
    return f"{remain // 60:02d}:{remain % 60:02d}"

# ---------- Запись в YAML ----------
def update_yaml_value(file_path: str, key: str, value: str) -> None:
    p = Path(file_path)
    text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
    # ^(пробелы)KEY(пробелы)=(пробелы)значение(возможный комментарий)
    pattern = re.compile(
        rf'^(\s*{re.escape(key)}\s*=\s*)(?P<val>[^\n#]*?)(?P<tail>\s*(#.*))?$',
        re.MULTILINE,
    )

    def repl(m: re.Match) -> str:
        old = (m.group("val") or "").strip()
        q = old[0] if len(old) >= 2 and old[0] in "\"'" and old[-1] == old[0] else None
        new_val = f"{q}{value}{q}" if q else value
        return m.group(1) + new_val + (m.group("tail") or "")

    if pattern.search(text):
        new_text = pattern.sub(repl, text, count=1)
    else:
        sep = "" if (not text or text.endswith("\n")) else "\n"
        new_text = f"{text}{sep}{key} = {value}\n"
    p.write_text(new_text, encoding="utf-8")

# ---------- main ----------
def main():
    w3 = get_web3_or_raise()
    lock_ts, close_ts = fetch_lock_close(w3)
    mmss = to_mmss(lock_ts, close_ts)
    update_yaml_value(SETTINGS_PATH, KEY_NAME, mmss)

if __name__ == "__main__":
    main()
