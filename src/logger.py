# src/logger.py
import logging
import os
from logging.handlers import TimedRotatingFileHandler


def setup_logger(log_dir='logs'):
    """Setup logging configuration with daily rotating file handler."""
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Create daily rotating file handler
    log_file = os.path.join(log_dir, 'scada_sms.log')
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30  # Keep logs for 30 days
    )
    file_handler.setLevel(logging.ERROR)  # Only log errors to file
    file_handler.setFormatter(file_formatter)
    file_handler.suffix = "%Y%m%d"  # Daily suffix format

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger