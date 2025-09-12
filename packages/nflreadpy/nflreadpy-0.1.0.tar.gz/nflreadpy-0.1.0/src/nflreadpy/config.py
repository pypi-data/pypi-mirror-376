"""Configuration management for nflreadpy."""

from enum import Enum
from importlib.metadata import version
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheMode(str, Enum):
    """Cache modes for data storage."""

    MEMORY = "memory"
    FILESYSTEM = "filesystem"
    OFF = "off"


class DataFormat(str, Enum):
    """Preferred data format for downloads."""

    PARQUET = "parquet"
    CSV = "csv"


class NflreadpyConfig(BaseSettings):
    """Configuration settings for nflreadpy."""

    # Cache settings
    cache_mode: CacheMode = Field(
        default=CacheMode.MEMORY,
        description="Cache mode: 'memory', 'filesystem', or 'off'",
        alias="NFLREADPY_CACHE",
    )

    cache_dir: Path = Field(
        default_factory=lambda: Path(user_cache_dir("nflreadpy")),
        description="Directory for filesystem cache",
        alias="NFLREADPY_CACHE_DIR",
    )

    cache_duration: int = Field(
        default=86400,
        description="Cache duration in seconds (default: 24 hours)",
        alias="NFLREADPY_CACHE_DURATION",
    )

    # Data preferences
    prefer_format: DataFormat = Field(
        default=DataFormat.PARQUET,
        description="Preferred data format: 'parquet' or 'csv'",
        alias="NFLREADPY_PREFER",
    )

    # Progress and logging
    verbose: bool = Field(
        default=True,
        description="Show progress messages",
        alias="NFLREADPY_VERBOSE",
    )

    # Request settings
    timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        alias="NFLREADPY_TIMEOUT",
    )

    user_agent: str = Field(
        default=f"nflverse/nflreadpy {version('nflreadpy')}",
        description="User agent for HTTP requests",
        alias="NFLREADPY_USER_AGENT",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


# Global configuration instance
config = NflreadpyConfig()


def get_config() -> NflreadpyConfig:
    """Get the current configuration."""
    return config


def update_config(**kwargs: Any) -> None:
    """Update configuration settings."""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")


def reset_config() -> None:
    """Reset configuration to defaults."""
    global config
    config = NflreadpyConfig()
