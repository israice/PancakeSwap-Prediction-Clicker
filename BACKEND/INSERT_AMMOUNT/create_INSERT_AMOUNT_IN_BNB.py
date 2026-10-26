import os
import sys
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

# ==================== НАСТРОЙКИ ====================

PROJECT_ROOT = Path(__file__).resolve().parent
DASHBOARD_PATH = PROJECT_ROOT / "DASHBOARD.py"

# ==================================================

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def calculate_amount(wallet_balance):
    balance_hundredths = int(wallet_balance * 100)
    amount = Decimal(balance_hundredths) / Decimal("1000")

    return max(amount, Decimal("0.001"))


def update_dashboard():
    try:
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        wallet_match = re.search(
            r"(?m)^\s*WALLET_BALANCE\s*=\s*([0-9]+(?:\.[0-9]+)?)",
            source,
        )

        amount_match = re.search(
            r"(?m)^(\s*INSERT_AMOUNT_IN_BNB\s*=\s*)([0-9]+(?:\.[0-9]+)?)",
            source,
        )

        if not wallet_match or not amount_match:
            return

        wallet_balance = Decimal(wallet_match.group(1))
        current_amount = Decimal(amount_match.group(2))

        new_amount = calculate_amount(wallet_balance)

        if new_amount == current_amount:
            return

        replacement = amount_match.group(1) + format(new_amount, ".3f")

        updated_source = (
            source[:amount_match.start()]
            + replacement
            + source[amount_match.end():]
        )

        DASHBOARD_PATH.write_text(updated_source, encoding="utf-8")

    except (OSError, InvalidOperation, ValueError):
        return


def main():
    update_dashboard()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass