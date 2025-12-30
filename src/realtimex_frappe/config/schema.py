"""Pydantic models for configuration validation."""

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from ..utils.paths import get_default_bench_path


class FrappeConfig(BaseModel):
    """Configuration for Frappe framework."""

    branch: str = "realtimex/v15.93.0"
    repo: str = "https://github.com/therealtimex/frappe.git"


class AppConfig(BaseModel):
    """Configuration for a Frappe app to install."""

    name: str
    url: str
    branch: str = "version-15"
    install: bool = True


class NodeBinaryConfig(BaseModel):
    """Configuration for bundled Node.js binary."""

    bin_dir: Optional[Path] = None
    """Path to the Node.js bin directory (contains node, npm, yarn)."""

    version: str = "18"
    """Expected Node.js version for documentation purposes."""


class WkhtmltopdfBinaryConfig(BaseModel):
    """Configuration for bundled wkhtmltopdf binary."""

    bin_dir: Optional[Path] = None
    """Path to the wkhtmltopdf bin directory."""


class BinariesConfig(BaseModel):
    """Configuration for all bundled binaries."""

    node: NodeBinaryConfig = Field(default_factory=NodeBinaryConfig)
    wkhtmltopdf: WkhtmltopdfBinaryConfig = Field(default_factory=WkhtmltopdfBinaryConfig)


class RedisConfig(BaseModel):
    """Configuration for Redis connection."""

    host: str = "127.0.0.1"
    cache_port: int = 13001
    """Port for Redis cache (redis_cache in Frappe)."""
    queue_port: int = 11001
    """Port for Redis queue (redis_queue in Frappe)."""
    use_external: bool = False
    """When True, skip starting Redis in Procfile (use existing running Redis)."""

    @property
    def cache_url(self) -> str:
        """Get Redis cache URL in the format expected by Frappe."""
        return f"redis://{self.host}:{self.cache_port}"

    @property
    def queue_url(self) -> str:
        """Get Redis queue URL in the format expected by Frappe."""
        return f"redis://{self.host}:{self.queue_port}"


class DatabaseConfig(BaseModel):
    """Configuration for database connection."""

    type: Literal["postgres", "mariadb"] = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    schema: Optional[str] = None
    """PostgreSQL schema name. When set, enables schema-based isolation 
    (no DROP/CREATE DATABASE). Used for Supabase compatibility."""

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Accept Supabase hosts like db.xxx.supabase.co."""
        return v.strip()

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Ensure port is valid."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("schema")
    @classmethod
    def validate_schema(cls, v: Optional[str]) -> Optional[str]:
        """Validate PostgreSQL schema name."""
        import re
        if v is None:
            return None
        v = v.strip().lower()
        if not v:
            return None
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError("Schema must be lowercase, start with letter, contain only [a-z0-9_]")
        if v in ('public', 'information_schema') or v.startswith('pg_'):
            raise ValueError(f"Cannot use reserved schema name: {v}")
        if len(v) > 63:
            raise ValueError("Schema name too long (max 63 chars)")
        return v


class SiteConfig(BaseModel):
    """Configuration for the Frappe site."""

    name: Optional[str] = None
    admin_password: Optional[str] = None


class BenchConfig(BaseModel):
    """Configuration for the bench installation."""

    path: str = Field(default_factory=get_default_bench_path)
    port: int = 8000
    """Webserver port for bench serve."""
    developer_mode: bool = True
    version: Optional[str] = None
    """Pinned bench version (e.g., 'v15.93.0'). If None, uses latest."""

    @field_validator("path", mode="before")
    @classmethod
    def validate_path(cls, v: str | None) -> str:
        """Use default path if null or empty is provided."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return get_default_bench_path()
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Ensure port is valid."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class RealtimexConfig(BaseModel):
    """Root configuration model for realtimex-frappe."""

    version: str = "1.0.0"
    frappe: FrappeConfig = Field(default_factory=FrappeConfig)
    apps: list[AppConfig] = Field(default_factory=list)
    binaries: BinariesConfig = Field(default_factory=BinariesConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    site: SiteConfig = Field(default_factory=SiteConfig)
    bench: BenchConfig = Field(default_factory=BenchConfig)

    def with_overrides(
        self,
        site_name: Optional[str] = None,
        admin_password: Optional[str] = None,
        db_host: Optional[str] = None,
        db_port: Optional[int] = None,
        db_name: Optional[str] = None,
        db_user: Optional[str] = None,
        db_password: Optional[str] = None,
        bench_path: Optional[str] = None,
    ) -> "RealtimexConfig":
        """Create a new config with CLI overrides applied."""
        data = self.model_dump()

        if site_name is not None:
            data["site"]["name"] = site_name
        if admin_password is not None:
            data["site"]["admin_password"] = admin_password
        if db_host is not None:
            data["database"]["host"] = db_host
        if db_port is not None:
            data["database"]["port"] = db_port
        if db_name is not None:
            data["database"]["name"] = db_name
        if db_user is not None:
            data["database"]["user"] = db_user
        if db_password is not None:
            data["database"]["password"] = db_password
        if bench_path is not None:
            data["bench"]["path"] = bench_path

        return RealtimexConfig.model_validate(data)
