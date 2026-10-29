from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]


class Settings(BaseSettings):
    # Application metadata
    app_name: str = "ShareSpace API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False
    api_v1_str: str = "/api/v1"

    # Security
    secret_key: str = Field(
        default="insecure-development-secret-key-replace-in-production",
        description="Application secret key used for session/token verification"
    )
    supabase_jwt_secret: Optional[str] = Field(
        default=None,
        description="Supabase JWT secret for verifying HS256 tokens in production"
    )
    supabase_jwt_public_key: Optional[str] = Field(
        default=None,
        description="PEM-encoded public key for asymmetric RS256/ES256 verification"
    )
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL (e.g. https://<ref>.supabase.co)"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm used for local dev test token generation (HS256, ES256, RS256)"
    )
    jwt_algorithms: Union[List[str], str] = Field(
        default=["ES256", "RS256", "HS256"],
        description="Allowlisted incoming JWT verification algorithms"
    )
    jwt_audience: Optional[str] = Field(
        default="authenticated",
        description="Expected JWT audience claim"
    )
    jwt_issuer: Optional[str] = Field(
        default=None,
        description="Expected JWT issuer claim"
    )

    # CORS configuration
    cors_origins: Union[List[str], str] = Field(
        default=DEFAULT_CORS_ORIGINS,
        description="Allowed CORS origins for browser clients",
    )
    cors_origin_regex: Optional[str] = Field(
        default=r"^https?://(localhost|127\.0\.0\.1):(517[3-9]|518[0-9]|3000)$",
        description="Regex pattern to match local development server ports dynamically",
    )

    # Database configuration (PostgreSQL ONLY)
    # None indicates that no database has been configured yet.
    database_url: Optional[str] = Field(
        default=None,
        description="Async PostgreSQL connection string (e.g. postgresql+asyncpg://user:pass@host:5432/dbname)"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_timeout: float = 5.0
    db_enforce_app_role: bool = Field(
        default=True,
        description="Enforce SET LOCAL ROLE sharespace_app on application sessions"
    )

    # Private Evidence Storage configuration
    evidence_storage_provider: str = Field(
        default="supabase",
        description="Object storage provider: 'supabase' or 's3'"
    )
    evidence_storage_bucket: Optional[str] = Field(
        default=None,
        description="Name of private object storage bucket"
    )
    supabase_bucket_name: Optional[str] = Field(
        default=None,
        description="Alias for evidence_storage_bucket"
    )
    supabase_service_role_key: Optional[str] = Field(
        default=None,
        description="Supabase service role key for authorized backend operations"
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        description="Supabase anon public key"
    )
    storage_signed_url_expiry: int = Field(
        default=3600,
        description="Expiry in seconds for private signed download URLs"
    )

    @property
    def resolved_storage_bucket(self) -> Optional[str]:
        return self.evidence_storage_bucket or self.supabase_bucket_name

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, str):
            # Split comma-separated string if provided via environment variable
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else DEFAULT_CORS_ORIGINS
        if isinstance(v, list):
            origins = [str(origin).strip() for origin in v if str(origin).strip()]
            return origins if origins else DEFAULT_CORS_ORIGINS
        return DEFAULT_CORS_ORIGINS

    @field_validator("jwt_algorithms", mode="before")
    @classmethod
    def assemble_jwt_algorithms(cls, v: object) -> List[str]:
        if isinstance(v, str):
            algs = [a.strip().upper() for a in v.split(",") if a.strip()]
            return algs if algs else ["ES256", "RS256", "HS256"]
        if isinstance(v, (list, tuple)):
            algs = [str(a).strip().upper() for a in v if str(a).strip()]
            return algs if algs else ["ES256", "RS256", "HS256"]
        return ["ES256", "RS256", "HS256"]

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        # Enforce PostgreSQL constraint
        url = v.strip()
        if not (url.startswith("postgresql://") or url.startswith("postgresql+asyncpg://") or url.startswith("postgresql+psycopg://")):
            raise ValueError(
                "ShareSpace strictly requires PostgreSQL. SQLite or other database engines are not supported."
            )
        return url

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
