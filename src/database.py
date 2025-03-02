# src/database.py
import logging
import pyodbc
from typing import List, Dict
from datetime import datetime
import pandas as pd


class DatabaseManager:
    def __init__(self, username: str, password: str, server: str = 'localhost', database: str = 'scada_db'):
        self.username = username
        self.password = password
        self.server = server
        self.database = database
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Establish database connection."""
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                "Trusted_Connection=no;"
            )
            return pyodbc.connect(conn_str)
        except pyodbc.Error as err:
            self.logger.error(f"Database connection failed: {err}")
            raise

    def is_sabbatical_holiday(self, date=None):
        """
        Check if given date is a Jewish holiday with sabbatical restrictions.

        Args:
            date: Date to check. If None, uses current date.

        Returns:
            bool: True if date is a sabbatical holiday, False otherwise.
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        elif isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')

        query = """
            SELECT is_sabbatical_holiday 
            FROM date_dimension 
            WHERE full_date = ?
        """

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, (date,))
            result = cursor.fetchone()

            if result and result[0] == 1:
                self.logger.info(f"Date {date} is a sabbatical holiday")
                return True

            self.logger.info(f"Date {date} is not a sabbatical holiday")
            return False

        except Exception as e:
            self.logger.error(f"Error checking if date is holiday: {e}")
            # If there's an error, assume it's not a holiday to avoid blocking notifications
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def get_sms_recipients(self, group_id: int, is_special_day: bool = None) -> List[Dict]:
        """
        Get SMS recipients for a given group.

        If current date is a sabbatical Jewish holiday, will only include
        users who have special_days_enabled=0 (users who work on holidays).

        Args:
            group_id: ID of the group to fetch recipients for
            is_special_day: Override holiday check with this value if provided

        Returns:
            List[Dict]: List of recipients with user_id and phone_number
        """
        # Check if today is a sabbatical holiday or use override if provided
        is_holiday = is_special_day if is_special_day is not None else self.is_sabbatical_holiday()
        self.logger.info(f"Current date holiday status: {is_holiday}")
        self.logger.info(f"get_sms_recipients called with group_id={group_id}, is_special_day={is_special_day}")
        # Base query for all recipients
        query = """
            SELECT u.phone_number, u.user_id
            FROM users u
            JOIN group_members gm ON u.user_id = gm.user_id
            WHERE gm.group_id = ?
            AND u.sms_enabled = 1
        """

        # Add holiday filter if it's a holiday
        if is_holiday:
            query += " AND u.special_days_enabled = 0"
            self.logger.info("Filtering SMS recipients to only those who work on holidays")

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, (group_id,))

            # Convert rows to list of dictionaries
            columns = [column[0] for column in cursor.description]
            recipients = [dict(zip(columns, row)) for row in cursor.fetchall()]

            self.logger.info(f"Found {len(recipients)} eligible SMS recipients for group {group_id}")
            return recipients
        except pyodbc.Error as err:
            self.logger.error(f"Failed to fetch SMS recipients: {err}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def log_sms_audit(self,
                      alarm_id: str,
                      user_id: int,
                      phone_number: str,
                      alarm_desc: str,
                      status: str,
                      message_status: str = None,
                      response: str = None):
        """Log SMS notification attempt to audit table."""

        if message_status and len(message_status) > 50:
            message_status = message_status[:47] + "..."

        if response and len(response) > 255:
            response = response[:250] + "..."

        query = """
            INSERT INTO sms_audit (
                alarm_id,
                user_id,
                phone_number,
                alarm_description,
                status,
                message_status,
                api_response,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, (alarm_id, user_id, phone_number, alarm_desc, status, message_status, response))
            conn.commit()
        except pyodbc.Error as err:
            self.logger.error(f"Failed to log audit entry: {err}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def import_date_dimension(self, date_df):
        """
        Import a pandas DataFrame of date dimension data into the SQL Server table.

        Args:
            date_df: pandas DataFrame with date dimension data
        """
        self.logger.info(f"Importing {len(date_df)} date records to database")

        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Clear existing data (optional, can be removed if you want to append)
            cursor.execute("DELETE FROM date_dimension")

            # Prepare insert statement
            insert_query = """
                INSERT INTO date_dimension (
                    date_id, full_date, day_of_week, day_name, day_of_month, 
                    day_of_year, week_of_year, month, month_name, quarter, year, 
                    is_weekend, hebrew_date, jewish_holiday, is_jewish_holiday, is_sabbatical_holiday
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Insert each row
            rows_inserted = 0
            for _, row in date_df.iterrows():
                # Handle optional columns that might be NaN
                jewish_holiday = row['jewish_holiday'] if 'jewish_holiday' in row and pd.notna(
                    row['jewish_holiday']) else None
                hebrew_date = row['hebrew_date'] if 'hebrew_date' in row and pd.notna(row['hebrew_date']) else None

                cursor.execute(
                    insert_query,
                    (
                        int(row['date_id']),
                        row['full_date'],
                        int(row['day_of_week']),
                        row['day_name'],
                        int(row['day_of_month']),
                        int(row['day_of_year']),
                        int(row['week_of_year']),
                        int(row['month']),
                        row['month_name'],
                        int(row['quarter']),
                        int(row['year']),
                        int(row['is_weekend']),
                        hebrew_date,
                        jewish_holiday,
                        int(row['is_jewish_holiday']),
                        int(row['is_sabbatical_holiday'])
                    )
                )
                rows_inserted += 1

                # Commit every 1000 rows
                if rows_inserted % 1000 == 0:
                    conn.commit()
                    self.logger.info(f"Inserted {rows_inserted} rows...")

            # Final commit
            conn.commit()
            self.logger.info(f"Successfully imported {rows_inserted} date records")

        except Exception as e:
            self.logger.error(f"Error importing date dimension: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()