
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database (SQLite per sviluppo, PostgreSQL per produzione)
    database_url: str = "sqlite+aiosqlite:///data/dealscout.db"
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    groq_api_key: str | None = None
    groq_model: str = "llama3-70b-8192"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Affiliate
    amazon_associates_tag: str = "dealscout-21"
    ebay_partner_network_id: str | None = None
    awin_api_key: str | None = None
    awin_publisher_id: str | None = None
    admitad_api_key: str | None = None
    impact_api_key: str | None = None
    rakuten_api_key: str | None = None

    # Social
    twitter_api_key: str | None = None
    twitter_api_secret: str | None = None
    twitter_access_token: str | None = None
    twitter_access_secret: str | None = None
    telegram_bot_token: str | None = None
    telegram_channel_id: str | None = None
    facebook_page_access_token: str | None = None
    facebook_page_id: str | None = None
    instagram_username: str | None = None
    instagram_password: str | None = None
    pinterest_access_token: str | None = None
    pinterest_board_id: str | None = None
    wordpress_url: str | None = None
    wordpress_username: str | None = None
    wordpress_app_password: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "DealScoutAI/0.1"
    mailchimp_api_key: str | None = None
    mailchimp_list_id: str | None = None

    # Proxy
    proxy_list: str | None = None
    proxy_rotate_interval: int = 300

    # Scraping
    max_concurrent_scrapes: int = 5
    scrape_frequency_hours: int = 6
    request_timeout: int = 30
    user_agent_rotate: bool = True

    # Deal filtering
    min_discount_percent: float = 20.0
    max_deal_age_days: int = 30
    price_history_days: int = 30

    # App
    log_level: str = "INFO"
    data_dir: str = "./data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
