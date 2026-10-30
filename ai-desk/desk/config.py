"""Settings from .env and config/limits.yaml. No defaults for secrets."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
VAR = ROOT / "var"                       # runtime state: risk state, journal, sqlite. Gitignored.
LIMITS_PATH = ROOT / "config" / "limits.yaml"
KILL_FILE = VAR / "KILL"                 # presence == kill switch engaged

load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    testnet: bool
    unified_collateral: bool            # spot USDC counts as margin (Unified account)
    account_address: str | None
    api_wallet_key: str | None
    telegram_token: str | None
    telegram_chat_id: str | None

    @property
    def base_url(self) -> str:
        """Execution endpoint."""
        from hyperliquid.utils import constants
        return constants.TESTNET_API_URL if self.testnet else constants.MAINNET_API_URL

    @property
    def data_url(self) -> str:
        """Market data always comes from mainnet: testnet has no volume, so its
        prices, funding and books say nothing. Paper and testnet execution both
        trade against real market state."""
        from hyperliquid.utils import constants
        return constants.MAINNET_API_URL


def settings() -> Settings:
    def opt(k: str) -> str | None:
        v = os.environ.get(k, "").strip()
        return v or None

    return Settings(
        testnet=os.environ.get("HL_TESTNET", "1") != "0",
        unified_collateral=os.environ.get("HL_UNIFIED_COLLATERAL", "0") == "1",
        account_address=opt("HL_ACCOUNT_ADDRESS"),
        api_wallet_key=opt("HL_API_WALLET_KEY"),
        telegram_token=opt("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=opt("TELEGRAM_CHAT_ID"),
    )


def load_limits(path: Path = LIMITS_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


VAR.mkdir(exist_ok=True)
