from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "ai-augmented-vuln-scanner"
    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    ollama_url: str = "http://ollama:11434"
    jwt_secret: str
    scan_concurrent_limit: int = 3
    nmap_default_profile: str = "normal"
    allowed_scopes: str = ""  # Comma-separated CIDR ranges, e.g. "10.0.0.0/8,192.168.0.0/16"
    nmap_profile_map: dict = {
        "stealth": "-T1 --scan-delay 2s",
        "normal": "-T3",
        "aggressive": "-T4 -A",
    }

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'  # Ignore extra environment variables
    )


settings = Settings()
