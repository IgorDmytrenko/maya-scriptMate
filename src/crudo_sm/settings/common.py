#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from pathlib import Path
import shutil

class JsonConfig:
    def __init__(self, path):
        """
        Initialize the JsonConfig class with the path to the JSON file.
        :param path: Path to the JSON config file.
        """
        self.path = path
        self.data = self._load_json()

    def _load_json(self):
        """Load the JSON file and return the data."""
        try:
            with open(self.path, 'r') as jsonfile:
                return json.load(jsonfile)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading JSON file: {e}")
            return None

    def reload(self):
        """Reload the JSON data from the file."""
        self.data = self._load_json()

    def get_param(self, object_name, value_name):
        """
        Get the value for the specified object and value name.
        :param object_name: The object to look up in the JSON data.
        :param value_name: The value name to extract from the specified object.
        :return: The requested value, or None if not found.
        """
        if not self.data:
            print("Error: JSON data is not loaded.")
            return None

        object_list = self.data.get(object_name)
        if not object_list or not isinstance(object_list, list):
            print(f"Error: Object '{object_name}' not found or is not a list.")
            return None

        for obj in object_list:
            if value_name in obj:
                return obj[value_name]

        print(f"Error: Value '{value_name}' not found in object '{object_name}'.")
        return None


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.current_directory = Path(__file__).parent
        self.core_config_file = (self.current_directory / "config.json").resolve()
        self.core_config = None
        self.local_config = None

        self._initialize_config()
        self._initialized = True

    def _initialize_config(self):
        """Initialize the configuration system, ensuring all necessary files exist."""
        self.core_config = JsonConfig(self.core_config_file)
        local_config_path_str = self.core_config.get_param('userSettings', 'path')
        if not local_config_path_str:
            raise ValueError("Could not find local config path in core config")

        self.local_config_path = Path(local_config_path_str).expanduser().resolve()
        self.local_config_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.local_config_path.exists():
            print(f"Local config not found. Creating at {self.local_config_path}")
            shutil.copy(self.core_config_file, self.local_config_path)

        self.local_config = JsonConfig(self.local_config_path)

    def reload(self):
        """Reload both core and local configs"""
        if self.core_config:
            self.core_config.reload()
        if self.local_config:
            self.local_config.reload()

    def get_local_param(self, object_name, value_name):
        """Get parameter from local config"""
        return self.local_config.get_param(object_name, value_name)

    def get_core_param(self, object_name, value_name):
        """Get parameter from core config"""
        return self.core_config.get_param(object_name, value_name)

    def get_local_config_data(self):
        """Get all data from local config file"""
        if self.local_config_path.exists():
            with open(self.local_config_path, 'r') as f:
                return json.load(f)
        return None

    def save_local_config_data(self, data):
        """Save data to local config file"""
        with open(self.local_config_path, 'w') as f:
            json.dump(data, f, indent=4)
        self.reload()

    def get_local_config_path(self):
        """Get the path to local config file"""
        return self.local_config_path

    def update_user_scripts_paths(self, network_path, local_path):
        """Update user scripts paths in local config"""
        data = self.get_local_config_data()
        if data and 'userScripts' in data:
            data['userScripts'][0]['network_path'] = network_path
            data['userScripts'][0]['local_path'] = local_path
            self.save_local_config_data(data)
            return True
        return False

CONFIG = ConfigManager()
