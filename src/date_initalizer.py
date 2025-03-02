# src/date_initializer.py
"""
Module for initializing the date dimension table with Jewish holidays.
This is called during database initialization.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
from database import DatabaseManager
from date_dimension import create_date_dimension


def initialize_date_dimension(db_manager: DatabaseManager, years_ahead: int = 99) -> None:
    """
    Initialize the date dimension table with Jewish holidays.

    Args:
        db_manager: DatabaseManager instance for database operations
        years_ahead: Number of years ahead to generate dates for
    """
    logger = logging.getLogger(__name__)

    try:
        # Check if date_dimension table is empty
        conn = db_manager.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM date_dimension")
        count = cursor.fetchone()[0]
        conn.close()

        # If table has data, we don't need to initialize it
        if count > 0:
            logger.info(f"Date dimension table already contains {count} records, skipping initialization")
            return

        # Generate dates from today to N years ahead
        today = datetime.now()
        start_date = today.strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=365 * years_ahead)).strftime('%Y-%m-%d')

        logger.info(f"Initializing date dimension table with dates from {start_date} to {end_date}")

        # Try to import pyluach
        try:
            import pyluach
        except ImportError:
            logger.error("The pyluach package is required. Skipping date dimension initialization.")
            logger.error("Please install pyluach with: pip install pyluach")
            logger.error("Then run initialize_date_dimension() manually to populate the table")
            return

        # Generate date dimension data
        date_df = create_date_dimension(start_date, end_date)

        # Count holidays for logging
        sabbatical_days = date_df[date_df['is_sabbatical_holiday'] == 1]
        logger.info(f"Generated {len(date_df)} days with {len(sabbatical_days)} sabbatical holidays")

        # Import to database
        logger.info("Loading date dimension data to database...")
        db_manager.import_date_dimension(date_df)
        logger.info("Date dimension initialization complete")

    except Exception as e:
        logger.error(f"Error initializing date dimension: {e}")
        logger.error("Date dimension table will be empty. You may need to populate it manually.")
