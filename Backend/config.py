# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTORSTORE_DIR: str = "../Github_dataset/vectorstore_dir"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DEFAULT_CHAT_MODEL: str = "gpt-4o-mini"

settings = Settings()
