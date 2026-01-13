import sys
from dotenv import load_dotenv
from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

ENV = sys.argv[1]

COST = {
    "witchcraft": 0,
    "reading": 33,
    "ai_portrait": 33,
    "daily_card": 33,
    "follow_up": 33,
}

YK_TRUSTED_NETWORKS = [
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.154.128/25",
    "77.75.156.11",
    "77.75.156.35",
    "2a02:5180::/32",
]


class YKPaymentsConfig(BaseModel):
    shop_id: str
    key: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f".env.{ENV}",
        env_prefix="BOT_",
        env_nested_delimiter="__",
    )
    token: str
    openai_api_key: str
    google_api_key: str
    database_url: str
    owners: set[str]

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    rubles_per_credit: int = 10
    yk: YKPaymentsConfig


settings = Settings()

bot = Bot(
    token=settings.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
