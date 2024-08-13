import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GH_TOKEN = os.getenv("GH_TOKEN", "")


settings = Settings()
