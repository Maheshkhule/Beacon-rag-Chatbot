import os
from dotenv import load_dotenv

load_dotenv()  # load .env

def get_env(key: str, default=None):
    return os.getenv(key, default)