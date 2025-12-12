from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8765
    api_key: str = "your-secret-api-key-here"
    enable_auth: bool = True
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_calls: int = 100
    rate_limit_period: int = 3600
    
    # Playwright Configuration
    headless: bool = True
    timeout: int = 30000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Cache Configuration
    cache_enabled: bool = True
    cache_ttl: int = 604800  # 7 days
    redis_url: Optional[str] = None
    
    # Search Configuration
    default_search_engine: str = "google"
    max_results_per_page: int = 10
    max_start_index: int = 91
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
