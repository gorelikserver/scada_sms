# src/config.py
import os
import sys
import json
import logging
from configparser import ConfigParser
from typing import Optional


class ConfigManager:
    def __init__(self, config_file: str = 'config.ini'):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.config = self._load_config()

    def _get_resource_path(self, filename: str) -> str:
        """Get resource path for both PyInstaller and normal execution."""
        if getattr(sys, '_MEIPASS', None):
            return os.path.join(sys._MEIPASS, filename)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    def _get_config_locations(self) -> list:
        """Get possible config file locations in priority order."""
        return [
            self.config_file,  # Explicit path
            os.path.join(os.getcwd(), 'config.ini'),  # Working directory
            self._get_resource_path('config.ini'),  # PyInstaller/package location
            os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False)
                                         else __file__), 'config.ini'),  # Executable/script directory
            os.environ.get('SCADA_SMS_CONFIG', '')  # Environment variable
        ]

    def _create_default_config(self, location: str) -> ConfigParser:
        """Create default configuration."""
        config = ConfigParser()
        config['database'] = {
            'username': 'default_user',
            'password': 'default_password',
            'server': 'localhost',
            'database': 'scada_db'
        }
        config['api'] = {
            'hostname': 'https://api.example.com',
            'params': json.dumps({
                "message": "message",
                "phone": "mobileNumber",
                "app": "application",
                "app_value": "SCADA"
            })
        }
        config['logging'] = {
            'log_dir': 'logs'
        }

        try:
            os.makedirs(os.path.dirname(location), exist_ok=True)
            with open(location, 'w') as f:
                config.write(f)
            self.logger.info(f"Created default config at: {location}")
        except Exception as e:
            self.logger.error(f"Failed to create default config: {e}")
            raise

        return config

    def _load_config(self) -> ConfigParser:
        """Load configuration from available locations."""
        config = ConfigParser()
        config_found = False

        for location in self._get_config_locations():
            if not location:
                continue

            if os.path.exists(location):
                try:
                    config.read(location)
                    self.logger.info(f"Loaded config from: {location}")
                    config_found = True
                    break
                except Exception as e:
                    self.logger.warning(f"Failed to load config from {location}: {e}")

        if not config_found:
            default_location = os.path.join(os.getcwd(), 'config.ini')
            config = self._create_default_config(default_location)

        return config

    def get(self, section: str, key: str, fallback: Optional[str] = None) -> Optional[str]:
        """Get configuration value."""
        try:
            return self.config[section][key]
        except Exception as e:
            self.logger.warning(f"Failed to get config {section}.{key}: {e}")
            return fallback

    def update(self, section: str, key: str, value: str) -> bool:
        """Update configuration value."""
        try:
            if section not in self.config:
                self.config[section] = {}

            self.config[section][key] = value

            # Try to update in multiple locations
            success = False
            for location in self._get_config_locations():
                if location and os.path.exists(os.path.dirname(location)):
                    try:
                        with open(location, 'w') as f:
                            self.config.write(f)
                        self.logger.info(f"Updated config at: {location}")
                        success = True
                        break
                    except Exception as e:
                        self.logger.warning(f"Failed to update config at {location}: {e}")

            if not success:
                raise Exception("No writable config location found")

            return True
        except Exception as e:
            self.logger.error(f"Failed to update config {section}.{key}: {e}")
            return False


# Global config instance
config_manager = ConfigManager()


# Compatibility functions
def load_config(config_file='config.ini'):
    """Compatibility function for existing code."""
    return ConfigManager(config_file).config


def update_config(section, key, value, config_file='config.ini'):
    """Compatibility function for existing code."""
    return ConfigManager(config_file).update(section, key, value)