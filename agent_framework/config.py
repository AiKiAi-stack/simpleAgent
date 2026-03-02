from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_api_key: str = "dummy"
    model_name: str = "Qwen/Qwen3-8B-Instruct"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    max_execution_time: int = 30
    log_dir: str = "logs"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
