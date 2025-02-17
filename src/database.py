# src/database.py
import logging
import pyodbc
from typing import List, Dict


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

    def get_sms_recipients(self, group_id: int) -> List[Dict]:
        query = """
            SELECT u.phone_number, u.user_id, g.group_name
            FROM users u
            JOIN group_members gm ON u.user_id = gm.user_id
            JOIN groups g ON g.group_id = gm.group_id
            WHERE gm.group_id = ?
            AND u.sms_enabled = 1
        """

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, (group_id,))

            # Convert rows to list of dictionaries
            columns = [column[0] for column in cursor.description]
            recipients = [dict(zip(columns, row)) for row in cursor.fetchall()]

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
                      alarm_desc: str,
                      status: str,
                      response: str):
        """Log SMS notification attempt to audit table."""
        query = """
            INSERT INTO sms_audit (
                alarm_id,
                user_id,
                alarm_description,
                status,
                api_response,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, GETDATE())
        """

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, (alarm_id, user_id, alarm_desc, status, response))
            conn.commit()
        except pyodbc.Error as err:
            self.logger.error(f"Failed to log audit entry: {err}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()