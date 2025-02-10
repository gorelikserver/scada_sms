Here's a more structured, clear, and professional rewrite of your README:  

---

# **SCADA SMS Notification System**  

A command-line tool for managing SCADA alarm notifications via SMS. This system queues alarms, manages recipient groups, and maintains an audit log of all notifications for tracking and troubleshooting.

---

## **Prerequisites**  

Ensure the following dependencies are installed before proceeding:  

- **Python**: Version **3.8** or higher  
- **SQL Server ODBC Driver 17**  
- **Microsoft Visual C++ Redistributable (2015-2019)**  
- **SQL Server Database** (for storing users, alarm queues, and logs)  

### **Required Installations**  
1. [Download ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)  
2. [Download Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)  

---

## **Installation**  

1. **Clone the repository and set up the virtual environment:**  

   ```bash
   git clone https://github.com/your-repository/scada-sms-system.git
   cd scada-sms-system

   # Create and activate virtual environment
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux

   # Install dependencies
   pip install -r requirements.txt
   ```

---

## **Configuration and Setup**  

### **1. Configure Database Connection**  
Set database credentials and connection details:  

```bash
python src/main.py set-db-credentials "your_username" "your_password"
python src/main.py set-db-connection "SERVER\INSTANCE" "database_name"
```

### **2. Configure SMS API Endpoint**  
Set the API URL for sending SMS notifications:  

```bash
python src/main.py set-api-hostname "https://your-sms-api.com"
```

### **3. Set API Parameters**  
Define how fields should be mapped when sending SMS messages:  

```bash
python src/main.py set-api-params '{"message": "message", "phone": "mobileNumber", "app": "application", "app_value": "SCADA"}'
```

### **4. Initialize the Database**  
Run the command below to create necessary tables:  

```bash
python src/main.py init-db
```

---

## **Usage**  

### **Send an Alarm Notification**  
Queue an alarm for a specific recipient group:  

```bash
python src/main.py send-alarm "Alarm message here" group_number
```

**Example:**  
```bash
python src/main.py send-alarm "High pressure detected in Pump Station 3" 5
```

### **Manually Process the Alarm Queue**  
Process all queued alarms and send SMS notifications:  

```bash
python src/main.py process-queue
```

---

## **Database Schema**  

### **Users Table**  
Stores user details, including phone numbers and SMS preferences.  

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

### **Group Members Table**  
Maps users to alarm recipient groups.  

```sql
CREATE TABLE group_members (
    group_member_id INT IDENTITY(1,1) PRIMARY KEY,
    group_number INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## **Configuration File Structure (`config.ini`)**  

The system configuration is stored in `config.ini`.  

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

---

## **Building an Executable**  

To package the application as a standalone executable:  

```bash
pip install pyinstaller
pyinstaller --onefile --name scada_sms src/main.py
```

The executable will be available in the `dist` folder.  

---

## **Logging and Error Handling**  

- **Logs** are stored in the configured directory (default: `logs/`)  
- **Daily Log Rotation** ensures long-term maintenance of logs  
- **Error Scenarios Handled**:  
  - Database connection failures  
  - SMS API request failures  
  - Configuration errors  
  - Queue processing issues  

Each error is logged with detailed context for troubleshooting.  

---

## **Security Best Practices**  

- **Secure the `config.ini` file** to prevent unauthorized access to credentials  
- **Use Windows Authentication** for SQL Server when possible  
- **Rotate database credentials periodically** for enhanced security  
- **Monitor logs regularly** to detect unauthorized access attempts  

---

## **Support & Troubleshooting**  

If you encounter issues:  
1. **Check logs** in the `logs/` directory for detailed error messages  
2. **Ensure database connectivity** (ODBC and SQL Server settings)  
3. **Verify API availability** (ensure the SMS API endpoint is accessible)  
4. **Confirm correct user permissions** in the SQL database  

For additional support, reach out to the system administrator or your IT department.  

---