# src/config.py
import os
from configparser import ConfigParser


def load_config(config_file='config.ini'):
    """Load configuration from INI file."""
    config = ConfigParser()

    # Create default config if it doesn't exist
    if not os.path.exists(config_file):
        config['database'] = {
            'username': 'default_user',
            'password': 'default_password',
            'server': 'localhost',
            'database': 'scada_db'
        }
        config['api'] = {
            'hostname': 'https://api.example.com'
        }
        config['logging'] = {
            'log_dir': 'logs'
        }
        with open(config_file, 'w') as f:
            config.write(f)

    config.read(config_file)
    return config


def update_config(section, key, value, config_file='config.ini'):
    """Update specific configuration value."""
    config = ConfigParser()
    config.read(config_file)

    if section not in config:
        config[section] = {}

    config[section][key] = value

    with open(config_file, 'w') as f:
        config.write(f)