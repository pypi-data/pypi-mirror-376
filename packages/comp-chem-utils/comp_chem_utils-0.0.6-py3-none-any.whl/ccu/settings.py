"""Global settings and configuration for ``ccu``."""

import logging
from logging import handlers
import os
from pathlib import Path
from typing import Any
from typing import ClassVar

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource
from pydantic_settings.sources import TomlConfigSettingsSource

logger = logging.getLogger(__name__)

CCU_HOME = Path(
    Path().home().expanduser(),
    ".config",
    "ccu",
)
_DEFAULT_CONFIG_FILE = Path(CCU_HOME, "config.toml")


class CCUSettings(BaseSettings):
    """Settings for Comp Chem Utils.

    All settings can be set and accessed programatically
    :data:`ccu.SETTINGS`, set using `CCU_` prefixed environment variables
    (e.g., `CCU_LOG_FILE`), or set in the `ccu` configuration file. The
    `ccu` configuration file is first searched for at `CCU_CONFIG_FILE`
    and then at `~/.config/ccu/config.toml`.

    .. seealso:: |sample-config-file|_

    .. |sample-config-file| replace:: sample configuration file
    """

    LOG_FILE: Path | None = Field(
        default=None,
        description="The filename for the log file. Note that this variable "
        "is mainly for storing state for application-like use. If you are "
        "using ccu as a library, you may be better served "
        "configuring handlers.",
    )
    LOG_LEVEL: int = Field(
        default=logging.DEBUG,
        description="The default log level.",
    )
    OUTPUT_ATOMS: str = Field(
        default="final.traj",
        description="the default file name to use for the output Atoms file",
    )
    TEMPLATE_DIR: Path | None = Field(
        default=None,
        description="If not None, specifies the directory to use to load "
        "templates",
    )

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="CCU_",
        case_sensitive=True,
        env_ignore_empty=True,
    )

    @field_validator("LOG_LEVEL", mode="plain")
    @classmethod
    def validate_log_level(cls, v: Any) -> int:
        """Validate the entered log level."""
        if isinstance(v, int):
            return v

        try:
            return getattr(logging, v)
        except AttributeError as err:
            msg = f"{v} not a valid logging level"
            raise ValueError(msg) from err
        except TypeError as err:
            msg = f"Unable to convert {v} into a logging level"
            raise ValueError(msg) from err

    @model_validator(mode="after")
    def configure_logging(self) -> "CCUSettings":
        """Configure logging based on user settings."""
        if self.LOG_FILE:
            fh = handlers.RotatingFileHandler(
                self.LOG_FILE,
                encoding="utf-8",
                maxBytes=int(1e6),
                backupCount=3,
            )
            log_format = (
                "%(asctime)s - %(name)s::%(funcName)s::%(lineno)s - "
                "%(levelname)s - %(message)s "
            )
            formatter = logging.Formatter(log_format)
            fh.setFormatter(formatter)
            fh.setLevel(level=self.LOG_LEVEL)
            logger.addHandler(fh)

        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Add a TOML configuration file to the settings sources.

        Note that the name of the TOML file can be set via environment
        variables. Otherwise, the default filename is used.
        """
        toml_file = os.environ.get("CCU_CONFIG_FILE", _DEFAULT_CONFIG_FILE)
        logger.info("Configuration file will be read from %s", toml_file)

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls, toml_file),
            file_secret_settings,
        )
