from os import getenv
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
ALLOWED_LEVELS: set[LogLevel] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings:
    """Encapsula e valida as configurações da biblioteca."""

    def __init__(self) -> None:
        self.root_dir: Path = Path(".").resolve()
        self.logs_dir: Path = self.root_dir / getenv("LOGS_DIR", "logs")
        self.logging_config_json_path: Path = Path(getenv("LOGGING_CONFIG_JSON", "default_logging.conf.json"))
        self.setup_logger_name: str = getenv("SETUP_LOGGER_NAME", "py_log_mjk.config_setup")
        self.setup_logger_level: LogLevel = self._validate_level(
            getenv("SETUP_LOGGER_LEVEL", "WARNING")
        )
        
        self.default_logger_level: LogLevel = self._validate_level(
            getenv("DEFAULT_LOGGER_LEVEL", "WARNING")
        )

    @staticmethod
    def _validate_level(level: str) -> LogLevel:
        if level not in ALLOWED_LEVELS:
            msg = f"Level {level!r} is not allowed. Use one of these: {ALLOWED_LEVELS}"
            raise ValueError(msg)
        return level

    def validate_paths(self) -> None:
        """Valida se os caminhos de diretórios e arquivos existem."""
        if not self.logs_dir.is_dir():
            self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.logging_config_json_path.is_file():
            pass


settings = Settings()