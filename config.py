import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass
class Settings:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    TWELVE_DATA_API_KEY: str = os.getenv("TWELVE_DATA_API_KEY")
    PAYPAL_EMAIL: str = os.getenv("PAYPAL_EMAIL", "")
    MPESA_PHONE: str = os.getenv("MPESA_PHONE", "")
    BINANCE_BNB: str = os.getenv("BINANCE_BNB", "")
    BINANCE_USDT: str = os.getenv("BINANCE_USDT", "")
    ADMIN_TELEGRAM_ID: int = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
    USERS_DB_PATH: str = os.getenv("USERS_DB_PATH", "data/users.json")
    TRIAL_DAYS: int = int(os.getenv("TRIAL_DAYS", "3"))
    PREMIUM_MONTH_DAYS: int = int(os.getenv("PREMIUM_MONTH_DAYS", "30"))
    PREMIUM_QUARTER_DAYS: int = int(os.getenv("PREMIUM_QUARTER_DAYS", "90"))
    PREMIUM_YEAR_DAYS: int = int(os.getenv("PREMIUM_YEAR_DAYS", "365"))

settings = Settings()