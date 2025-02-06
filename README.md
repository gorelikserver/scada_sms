# SCADA SMS Notification System

A command-line interface (CLI) tool for sending SMS notifications triggered by SCADA alarms. The system queues alarms, manages recipients by groups, and maintains an audit trail of all notifications.

## Prerequisites

- Python 3.8 or higher
- SQL Server ODBC Driver 17
- Microsoft Visual C++ Redistributable 2015-2019
- SQL Server Database

## Installation

1. Install required ODBC drivers and dependencies:
   - [Microsoft ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
   - [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

2. Clone the repository and set up Python environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Initial Setup

1. Set database credentials:
```bash
python src/main.py set-db-credentials "your_username" "your_password"
```

2. Configure database connection:
```bash
python src/main.py set-db-connection "SERVER\INSTANCE" "database_name"
```

3. Set SMS API endpoint:
```bash
python src/main.py set-api-hostname "https://your-sms-api.com"
```

4. Initialize database tables:
```bash
python src/main.py init-db
```

## Usage

### Send Alarm
```bash
python src/main.py send-alarm "Alarm message here" group_number
```

Example:
```bash
python src/main.py send-alarm "High pressure detected in Pump Station 3" 5
```

### Process Queue Manually
```bash
python src/main.py process-queue
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    sms_enabled BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE()
);
```

### Group Members Table
```sql
CREATE TABLE group_members (
    group_member_id INT IDENTITY(1,1) PRIMARY KEY,
    group_number INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

## Configuration

The system uses a config.ini file with the following structure:
```ini
[database]
username = your_username
password = your_password
server = SERVER\INSTANCE
database = database_name

[api]
hostname = https://your-sms-api.com

[logging]
log_dir = logs
```

## Building Executable

To create a standalone executable:
```bash
pip install pyinstaller
pyinstaller build.spec
```

The executable will be created in the `dist` directory.

## Logging

- Logs are stored in the configured log directory (default: 'logs')
- Error logs are automatically rotated daily
- Contains detailed information about alarm processing and SMS sending attempts

## Error Handling

The system handles various error scenarios:
- Database connection issues
- SMS API failures
- Queue processing errors
- Configuration problems

Each error is logged with appropriate context for troubleshooting.

## Security Notes

- Store the config.ini file in a secure location
- Use Windows Authentication when possible
- Regularly rotate database credentials
- Monitor audit logs for unauthorized access attempts

## Support

For issues and support:
1. Check the logs directory for detailed error information
2. Verify SQL Server and ODBC driver installation
3. Ensure proper network connectivity to SMS API
4. Confirm database permissions are correctly set
