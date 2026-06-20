from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""

    # VAPID (Web Push)
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_email: str = ""

    # Solar APIs
    growatt_api_key: str = ""
    solis_api_key: str = ""
    solis_api_secret: str = ""
    huawei_api_key: str = ""

    # Security
    encryption_key: str = ""
    admin_secret_key: str = ""
    admin_user_ids: str = ""
    admin_alert_webhook_url: str = ""

    # App
    railway_environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
