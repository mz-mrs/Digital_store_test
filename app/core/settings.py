from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_db: str = "digital_store"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    rabbitmq_user: str
    rabbitmq_password: str
    rabbitmq_host: str
    rabbitmq_port: int

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    provider_a_url: str = "http://127.0.0.1:8001"
    provider_b_url: str = "http://127.0.0.1:8002"

    api_url: str = 'http://127.0.0.1:8000'
    webhook_url:str = "http://127.0.0.1:8000/webhook/payment"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()