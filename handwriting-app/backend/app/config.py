from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central app config. Values are read from environment variables / a .env
    file so nothing sensitive lives in source control.
    """

    app_name: str = "Handwriting Synthesis API"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/handwriting"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Object storage for glyph images/SVGs (S3-compatible: AWS S3, R2, MinIO, etc.)
    storage_bucket: str = "handwriting-glyphs-dev"
    storage_endpoint_url: str | None = None  # set for MinIO/R2, leave None for AWS
    storage_access_key: str = ""
    storage_secret_key: str = ""

    # How many enrollment sheets the user must complete
    required_sheets: int = 3

    # Confidence threshold below which a segmented glyph is flagged for
    # human review instead of auto-accepted
    classifier_confidence_threshold: float = 0.55

    class Config:
        env_file = ".env"


settings = Settings()
