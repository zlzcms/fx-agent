import json
import os
from typing import Any, Dict, List, Optional, Union

import yaml


class SQLConfig:
    """
    Class for managing SQL configurations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SQL configuration.

        Args:
            config: Initial configuration dictionary
        """
        self.config = config or {}

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SQLConfig":
        """
        Create a configuration from a dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            SQLConfig instance
        """
        return cls(config_dict)

    @classmethod
    def from_json(cls, json_str: str) -> "SQLConfig":
        """
        Create a configuration from a JSON string.

        Args:
            json_str: JSON string

        Returns:
            SQLConfig instance
        """
        return cls(json.loads(json_str))

    @classmethod
    def from_json_file(cls, file_path: str) -> "SQLConfig":
        """
        Create a configuration from a JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            SQLConfig instance
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "SQLConfig":
        """
        Create a configuration from a YAML string.

        Args:
            yaml_str: YAML string

        Returns:
            SQLConfig instance
        """
        return cls(yaml.safe_load(yaml_str))

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "SQLConfig":
        """
        Create a configuration from a YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            SQLConfig instance
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the configuration.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the configuration.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update the configuration with a dictionary.

        Args:
            config_dict: Dictionary to update with
        """
        self.config.update(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config

    def to_json(self) -> str:
        """
        Convert the configuration to a JSON string.

        Returns:
            JSON string
        """
        return json.dumps(self.config, indent=2)

    def to_json_file(self, file_path: str) -> None:
        """
        Save the configuration to a JSON file.

        Args:
            file_path: Path to JSON file
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def to_yaml(self) -> str:
        """
        Convert the configuration to a YAML string.

        Returns:
            YAML string
        """
        return yaml.dump(self.config)

    def to_yaml_file(self, file_path: str) -> None:
        """
        Save the configuration to a YAML file.

        Args:
            file_path: Path to YAML file
        """
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f)

    def validate_required_keys(self, required_keys: List[str]) -> bool:
        """
        Validate that all required keys are present in the configuration.

        Args:
            required_keys: List of required keys

        Returns:
            True if all required keys are present, False otherwise
        """
        for key in required_keys:
            if key not in self.config:
                return False
        return True
