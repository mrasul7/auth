from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict
)


class Settings(BaseSettings):
    DB_URL: str 
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str 
    
    model_config = SettingsConfigDict(
        env_file=".env"
    )
    
    
settings = Settings()
