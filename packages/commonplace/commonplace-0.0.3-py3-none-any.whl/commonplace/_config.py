"""
Configuration management for the commonplace application.

Defines the Config class for handling application settings from
environment variables, .env files, and direct instantiation.
"""

import getpass
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import DirectoryPath, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG = Path(user_config_dir("commonplace")) / "commonplace.toml"
DEFAULT_NAME = getpass.getuser().title()  # Get the current user's name for default human-readable name
DEFAULT_EDITOR = "vim"


class Config(BaseSettings):
    """
    Configuration settings for the commonplace application.

    Settings can be provided via:
    - Environment variables (prefixed with COMMONPLACE_)
    - .env file in the current directory
    - Direct instantiation with keyword arguments

    Example:
        # Via environment variable
        export COMMONPLACE_ROOT=/home/user/commonplace

        # Via .env file
        COMMONPLACE_ROOT=/home/user/commonplace
        COMMONPLACE_WRAP=120
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_prefix="COMMONPLACE_",
        toml_file=DEFAULT_CONFIG,
    )

    root: DirectoryPath = Field(
        description="The root directory for storing commonplace data",
    )
    user: str = Field(default=DEFAULT_NAME, description="Human-readable name for the user e.g., Joe")
    wrap: int = Field(default=80, description="Target characters per line for text wrapping")
    editor: str = Field(default=DEFAULT_EDITOR, description="Default editor for opening notes")

    @field_validator("root", mode="before")
    @classmethod
    def validate_root_not_empty(cls, v):
        if isinstance(v, str) and v.strip() == "":
            raise ValueError("Root path cannot be empty")
        return v

    @model_validator(mode="before")
    def defaults_based_on_root(cls, values):
        """
        Set default values based on the root directory.
        If root is a string, convert it to a Path object.
        """
        return values


if __name__ == "__main__":
    print(Config.model_validate({}))
