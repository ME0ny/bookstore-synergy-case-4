import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Settings:
    YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
    YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET")
    YANDEX_REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI")
    PROTECTED_BOOKS_DIR = os.getenv("PROTECTED_BOOKS_DIR")
settings = Settings()


print(f"YANDEX_CLIENT_ID: {settings.YANDEX_CLIENT_ID}")
print(f"YANDEX_CLIENT_SECRET: {settings.YANDEX_CLIENT_SECRET}")
print(f"YANDEX_REDIRECT_URI: {settings.YANDEX_REDIRECT_URI}")

