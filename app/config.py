
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://educational_rag_user:SL1ZBHDpyU9EllszGY1ATnNKTUBkwCRp@dpg-d4lbbvkhg0os73b64fm0-a.oregon-postgres.render.com/educational_rag"
    SECRET_KEY: str = "SL1ZBHDpyU9EllszGY1ATnNKTUBkwCRp"
    GOOGLE_CLIENT_ID: str = "13518453378-t7totj1v60bam93dfvdp9eleapmalar1.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = "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"

    class Config:
        env_file = ".env"

settings = Settings()
