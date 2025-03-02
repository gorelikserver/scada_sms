# src/db_init.py
import logging
from database import DatabaseManager
from src.date_initalizer import initialize_date_dimension


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
        special_days_enabled BIT DEFAULT 0,
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
        alarm_id VARCHAR(100) NOT NULL,
        user_id INT NOT NULL,
        phone_number VARCHAR(100),
        alarm_description NVARCHAR(MAX) NOT NULL,
        status NVARCHAR(200) NOT NULL,
        message_status VARCHAR(200),
        api_response NVARCHAR(MAX),
        created_at DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    -- Create date_dimension table if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='date_dimension' AND xtype='U')
    CREATE TABLE date_dimension (
        date_id INT PRIMARY KEY,
        full_date DATE NOT NULL,
        day_of_week TINYINT NOT NULL,
        day_name VARCHAR(10) NOT NULL,
        day_of_month TINYINT NOT NULL,
        day_of_year SMALLINT NOT NULL,
        week_of_year TINYINT NOT NULL,
        month TINYINT NOT NULL,
        month_name VARCHAR(10) NOT NULL,
        quarter TINYINT NOT NULL,
        year SMALLINT NOT NULL,
        is_weekend BIT NOT NULL,
        hebrew_date VARCHAR(50) NULL,
        jewish_holiday VARCHAR(100) NULL,
        is_jewish_holiday BIT NOT NULL DEFAULT 0,
        is_sabbatical_holiday BIT NOT NULL DEFAULT 0
    );
    """

    indexes_sql = """
    -- Add indexes if they don't exist
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_users_phone')
    CREATE INDEX idx_users_phone ON users(phone_number);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_users_sms_enabled')
    CREATE INDEX idx_users_sms_enabled ON users(sms_enabled);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_users_special_days')
    CREATE INDEX idx_users_special_days ON users(special_days_enabled);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_group_members_group')
    CREATE INDEX idx_group_members_group ON group_members(group_id);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_group_members_user')
    CREATE INDEX idx_group_members_user ON group_members(user_id);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sms_audit_alarm_id')
    CREATE INDEX idx_sms_audit_alarm_id ON sms_audit(alarm_id);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sms_audit_created_at')
    CREATE INDEX idx_sms_audit_created_at ON sms_audit(created_at);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sms_audit_phone')
    CREATE INDEX idx_sms_audit_phone ON sms_audit(phone_number);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sms_audit_status')
    CREATE INDEX idx_sms_audit_status ON sms_audit(message_status);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_date_dimension_full_date')
    CREATE UNIQUE INDEX idx_date_dimension_full_date ON date_dimension(full_date);

    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_date_dimension_sabbatical')
    CREATE INDEX idx_date_dimension_sabbatical ON date_dimension(is_sabbatical_holiday);
    """

    # Check for new columns in existing tables
    alter_table_sql = """
    -- Add special_days_enabled column if it doesn't exist
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'special_days_enabled'
    )
    ALTER TABLE users ADD special_days_enabled BIT DEFAULT 0;

    -- Add phone_number column to audit table if it doesn't exist
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'sms_audit' AND COLUMN_NAME = 'phone_number'
    )
    ALTER TABLE sms_audit ADD phone_number VARCHAR(20);

    -- Add message_status column to audit table if it doesn't exist
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'sms_audit' AND COLUMN_NAME = 'message_status'
    )
    ALTER TABLE sms_audit ADD message_status VARCHAR(50);
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

        # Add new columns to existing tables
        logger.info("Checking for schema updates...")
        for statement in alter_table_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)

        # Create indexes
        logger.info("Creating indexes...")
        for statement in indexes_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)

        conn.commit()
        logger.info("Database schema initialization completed successfully")

        # Initialize date dimension table
        logger.info("Initializing date dimension data...")
        initialize_date_dimension(db_manager)

    except Exception as err:
        logger.error(f"Database initialization failed: {err}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()