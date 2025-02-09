import yaml
from typing import Any, Dict, List, Union

class ConfigLoader:
    """Loads and parses a YAML configuration file into structured objects, preserving dictionaries for lists."""

    def __init__(self, config_file: str):
        """
        Reads the YAML file and initializes configuration attributes.
        
        Args:
            config_file (str): Path to the YAML file.
        """
        self._load_yaml(config_file)
        self._initialize_attributes()

    def _load_yaml(self, config_file: str):
        """Reads the YAML file and stores its contents."""
        with open(config_file, "r") as file:
            self.config = yaml.safe_load(file)

    def _initialize_attributes(self):
        """Assigns YAML keys as attributes and handles nested dictionaries intelligently."""
        for key, value in self.config.items():
            setattr(self, key, self._convert_to_object(value))

    def _convert_to_object(self, value: Any) -> Any:
        """
        Recursively converts dictionaries into objects while ensuring list elements remain accessible.
        
        Args:
            value (Any): Value from the YAML configuration.

        Returns:
            Any: Object for dictionaries, raw lists for lists, or unchanged value.
        """
        if isinstance(value, dict):
            # If the dictionary contains lists or further dictionaries, leave it as a dictionary
            return value if any(isinstance(v, (dict, list)) for v in value.values()) else ConfigObject(value)
        elif isinstance(value, list):
            # Recursively convert dictionary elements within lists to objects
            return [self._convert_to_object(item) if isinstance(item, dict) else item for item in value]
        else:
            return value

    def __repr__(self):
        """Returns a readable representation of the loaded configuration."""
        return f"<ConfigLoader {self.config}>"

class ConfigObject:
    """Helper class to allow dot-access for dictionary attributes."""
    def __init__(self, dictionary: Dict[str, Any]):
        self.__dict__.update(dictionary)

    def __repr__(self):
        return f"<ConfigObject {self.__dict__}>"

