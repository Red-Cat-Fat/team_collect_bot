import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    admin_ids: list[int]
    topic_id: int
    db_path: str
    timezone: str

    @classmethod
    def from_env(cls) -> "Config":
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]

        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            admin_ids=admin_ids,
            topic_id=int(os.getenv("TOPIC_ID", "0")),
            db_path=os.getenv("DB_PATH", "./data/bot.db"),
            timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
        )


config = Config.from_env()