import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # DB Config
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Auth Config
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

config = Config()
