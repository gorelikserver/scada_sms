# src/db_init.py
import logging
from database import DatabaseManager


def init_database(db_manager: DatabaseManager):
    """Initialize database tables."""
    tables_sql = """
    -- Create users table if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
    CREATE TABLE users (
        user_id INT IDENTITY(1,1) PRIMARY KEY,
        phone_number VARCHAR(20) NOT NULL,
        user_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        role VARCHAR(255) NOT NULL,
        sms_enabled BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE()
    );

    -- Create groups table if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='groups' AND xtype='U')
    CREATE TABLE groups (
        group_id INT IDENTITY(1,1) PRIMARY KEY,
        group_name VARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT GETDATE()
    );

    -- Create group_members table if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='group_members' AND xtype='U')
    CREATE TABLE group_members (
        group_member_id INT IDENTITY(1,1) PRIMARY KEY,
        group_id INT NOT NULL,
        user_id INT NOT NULL,
        created_at DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (group_id) REFERENCES groups(group_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    -- Create audit table if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sms_audit' AND xtype='U')
    CREATE TABLE sms_audit (
        audit_id INT IDENTITY(1,1) PRIMARY KEY,
        alarm_id VARCHAR(50) NOT NULL,
        user_id INT NOT NULL,
        alarm_description NVARCHAR(MAX) NOT NULL,
        status VARCHAR(20) NOT NULL,
        api_response NVARCHAR(MAX),
        created_at DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """

    indexes_sql = """
    -- Add indexes if they don't exist
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_users_phone')
    CREATE INDEX idx_users_phone ON users(phone_number);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_users_sms_enabled')
    CREATE INDEX idx_users_sms_enabled ON users(sms_enabled);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_group_members_group')
    CREATE INDEX idx_group_members_group ON group_members(group_id);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_group_members_user')
    CREATE INDEX idx_group_members_user ON group_members(user_id);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sms_audit_alarm_id')
    CREATE INDEX idx_sms_audit_alarm_id ON sms_audit(alarm_id);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sms_audit_created_at')
    CREATE INDEX idx_sms_audit_created_at ON sms_audit(created_at);
    """


    logger = logging.getLogger(__name__)

    try:
        conn = db_manager.connect()
        cursor = conn.cursor()

        # Create tables
        logger.info("Creating tables...")
        for statement in tables_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)

        # Create indexes
        logger.info("Creating indexes...")
        for statement in indexes_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)

        conn.commit()
        logger.info("Database initialization completed successfully")

    except Exception as err:
        logger.error(f"Database initialization failed: {err}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()
