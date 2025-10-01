"""YAML configuration parser."""

import logging
from pathlib import Path
from typing import Any, Dict, Union

import yaml
from pydantic import ValidationError

from kubeagentic.config.schema import AgentConfigSchema
from kubeagentic.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigParser:
    """Parse and validate YAML configuration files."""

    @staticmethod
    def parse_file(file_path: Union[str, Path]) -> AgentConfigSchema:
        """
        Parse a YAML configuration file.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            Validated configuration schema

        Raises:
            ConfigurationError: If file cannot be read or is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")

        if not file_path.is_file():
            raise ConfigurationError(f"Path is not a file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to read configuration file: {e}") from e

        return ConfigParser.parse_dict(raw_config, source=str(file_path))

    @staticmethod
    def parse_dict(config_dict: Dict[str, Any], source: str = "dict") -> AgentConfigSchema:
        """
        Parse a configuration dictionary.

        Args:
            config_dict: Configuration as a dictionary
            source: Source description for error messages

        Returns:
            Validated configuration schema

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not isinstance(config_dict, dict):
            raise ConfigurationError(f"Configuration must be a dictionary, got {type(config_dict)}")

        try:
            config = AgentConfigSchema(**config_dict)
            logger.info(f"Successfully parsed configuration from {source}")
            return config
        except ValidationError as e:
            error_msg = ConfigParser._format_validation_errors(e)
            raise ConfigurationError(
                f"Configuration validation failed for {source}:\n{error_msg}"
            ) from e
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration from {source}: {e}") from e

    @staticmethod
    def parse_yaml_string(yaml_string: str) -> AgentConfigSchema:
        """
        Parse a YAML configuration string.

        Args:
            yaml_string: YAML configuration as string

        Returns:
            Validated configuration schema

        Raises:
            ConfigurationError: If YAML is invalid
        """
        try:
            config_dict = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML string: {e}") from e

        return ConfigParser.parse_dict(config_dict, source="yaml_string")

    @staticmethod
    def _format_validation_errors(error: ValidationError) -> str:
        """
        Format Pydantic validation errors in a readable way.

        Args:
            error: Pydantic ValidationError

        Returns:
            Formatted error message
        """
        errors = []
        for err in error.errors():
            location = " -> ".join(str(loc) for loc in err["loc"])
            message = err["msg"]
            errors.append(f"  • {location}: {message}")

        return "\n".join(errors)

    @staticmethod
    def validate_file(file_path: Union[str, Path]) -> tuple[bool, str]:
        """
        Validate a configuration file without fully parsing it.

        Args:
            file_path: Path to YAML configuration file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ConfigParser.parse_file(file_path)
            return True, "Configuration is valid"
        except ConfigurationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}" 