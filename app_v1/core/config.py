from dotenv import load_dotenv
from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()


COST = {
    "witchcraft": 10,
    "reading": 1,
    "ai_portrait": 2,
    "daily_card": 2,
    "follow_up": 1,
}


class YKPaymentsConfig(BaseModel):
    test_shop_id: str
    test_key: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BOT_",
        env_nested_delimiter="__",
    )
    token: str
    openai_api_key: str
    google_api_key: str
    database_url: str
    admins: set[str]

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
