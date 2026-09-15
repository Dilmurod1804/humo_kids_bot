"""
Humo Kids bot uchun konfiguratsiya.
Barcha sozlamalar .env faylidan o'qiladi (pydantic-settings orqali).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram bot tokeni (@BotFather dan olinadi)
    bot_token: str

    # Ma'lumotlar bazasi manzili (SQLite yoki PostgreSQL bo'lishi mumkin)
    # SQLite misoli:      sqlite+aiosqlite:///./humo_kids.db
    # PostgreSQL misoli:  postgresql+asyncpg://user:password@db:5432/humo_kids
    database_url: str = "sqlite+aiosqlite:///./humo_kids.db"

    # Admin panelga kirish kodi (harf va sondan iborat, masalan: Admin2026)
    admin_access_code: str

    # Channel Service (backend) manzili
    channel_service_url: str = "http://channel_service:8001"

    # Bot va Channel Service o'rtasidagi ichki so'rovlarni himoyalash uchun token
    internal_api_token: str

    # Taomnoma va dars jadvali necha soatdan keyin avtomatik o'chirilishi
    menu_schedule_ttl_hours: int = 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
