
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://educational_rag_user:SL1ZBHDpyU9EllszGY1ATnNKTUBkwCRp@dpg-d4lbbvkhg0os73b64fm0-a.oregon-postgres.render.com/educational_rag"
    secret_key: str = "SL1ZBHDpyU9EllszGY1ATnNKTUBkwCRp"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    google_client_id: str = "13518453378-t7totj1v60bam93dfvdp9eleapmalar1.apps.googleusercontent.com"
    google_client_secret: str = "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"
    openai_api_key: str = "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"
    gemini_api_key: str = ""
    # Disable heavy RAG retrieval (embeddings/vector-store downloads) by default.
    enable_rag_retrieval: bool = True
    app_env: str = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
