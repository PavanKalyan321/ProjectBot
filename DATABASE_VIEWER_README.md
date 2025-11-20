# Database Table Viewer Dashboard

A web-based dashboard for viewing and exploring database tables on DigitalOcean droplets. Supports PostgreSQL and MySQL databases with an intuitive interface for browsing tables, viewing schemas, and executing queries.

## Features

- **Multi-Database Support**: Connect to PostgreSQL and MySQL databases
- **Table Browser**: View all tables with row counts and column information
- **Schema Viewer**: Inspect table structures, data types, and constraints
- **Data Viewer**: Browse table data with pagination and sorting
- **Query Executor**: Run custom SELECT queries with results display
- **CSV Export**: Export table data to CSV files
- **Real-time Updates**: Live connection status and data refresh
- **Responsive UI**: Modern, clean interface with dark gradient theme

## Installation

### 1. Install Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt
```

This will install:
- `sqlalchemy>=1.4.0` - SQL toolkit and ORM
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter
- `pymysql>=1.0.0` - MySQL adapter
- `flask>=2.0.0` - Web framework
- `flask-socketio>=5.0.0` - Real-time updates
- `pandas>=1.3.0` - Data processing

### 2. Configure Database Connections

Edit the configuration file at `backend/dashboard/db_config.json`:

```json
{
  "connections": [
    {
      "name": "Production PostgreSQL",
      "type": "postgresql",
      "host": "your-droplet-ip",
      "port": 5432,
      "database": "your_database",
      "username": "your_username",
      "password": "your_password",
      "ssh_tunnel": false,
      "ssh_host": "",
      "ssh_port": 22,
      "ssh_user": "",
      "ssh_key_path": ""
    },
    {
      "name": "Dev MySQL",
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "dev_db",
      "username": "root",
      "password": "password",
      "ssh_tunnel": false,
      "ssh_host": "",
      "ssh_port": 22,
      "ssh_user": "",
      "ssh_key_path": ""
    }
  ]
}
```

**Connection Parameters:**

- `name`: Display name for the connection
- `type`: Database type (`postgresql` or `mysql`)
- `host`: Database host (IP address or domain)
- `port`: Database port (5432 for PostgreSQL, 3306 for MySQL)
- `database`: Database name to connect to
- `username`: Database user
- `password`: Database password
- `ssh_tunnel`: Enable SSH tunneling (not yet implemented)

### 3. Set Up Database on DigitalOcean Droplet

If you don't have a database set up yet:

#### PostgreSQL

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE your_database;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_database TO your_username;
\q
EOF

# Allow remote connections (if needed)
sudo nano /etc/postgresql/*/main/postgresql.conf
# Change: listen_addresses = '*'

sudo nano /etc/postgresql/*/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql

# Open firewall
sudo ufw allow 5432/tcp
```

#### MySQL

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Install MySQL
sudo apt update
sudo apt install mysql-server -y

# Start MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation

# Create database and user
sudo mysql << EOF
CREATE DATABASE your_database;
CREATE USER 'your_username'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON your_database.* TO 'your_username'@'%';
FLUSH PRIVILEGES;
EXIT;
EOF

# Allow remote connections
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# Change: bind-address = 0.0.0.0

sudo systemctl restart mysql

# Open firewall
sudo ufw allow 3306/tcp
```

## Usage

### Starting the Dashboard

```bash
# Run with default settings (localhost:5002)
python3 run_database_viewer.py

# Or specify custom host and port
python3 run_database_viewer.py --host 0.0.0.0 --port 8080
```

The dashboard will be available at:
- Local: `http://localhost:5002`
- Network: `http://your-server-ip:5002`

### Using the Dashboard

#### 1. Connect to Database

1. Click on a database connection in the left sidebar
2. Wait for the connection to establish (green "Connected" badge)
3. Tables will automatically load

#### 2. Browse Tables

1. Click on a table in the "Tables" panel
2. The "Data" tab shows paginated table content
3. Click column headers to sort
4. Use pagination controls to navigate

#### 3. View Schema

1. Select a table
2. Click the "Schema" tab
3. View column details:
   - Column name and data type
   - Nullable status
   - Default values
   - Primary keys and indexes

#### 4. Execute Queries

1. Click the "Query" tab
2. Enter your SELECT query:
   ```sql
   SELECT * FROM users WHERE created_at > '2024-01-01' LIMIT 10;
   ```
3. Click "Execute Query"
4. View results in a table

**Note:** Only SELECT queries are allowed for security.

#### 5. Export Data

1. Select a table in the "Data" tab
2. Click "Export to CSV"
3. Download will start automatically

## Security Best Practices

### 1. Firewall Configuration

Only allow database access from trusted IPs:

```bash
# PostgreSQL - allow only from specific IP
sudo ufw delete allow 5432/tcp
sudo ufw allow from your-app-server-ip to any port 5432

# MySQL - allow only from specific IP
sudo ufw delete allow 3306/tcp
sudo ufw allow from your-app-server-ip to any port 3306
```

### 2. Use Strong Passwords

```bash
# Generate strong password
openssl rand -base64 32
```

### 3. SSL/TLS Connections

For production, use SSL connections:

**PostgreSQL:**
```json
{
  "name": "Secure PostgreSQL",
  "type": "postgresql",
  "host": "your-droplet-ip",
  "port": 5432,
  "database": "your_database",
  "username": "your_username",
  "password": "your_password"
}
```

Then modify connection string in code to add `sslmode=require`.

### 4. Read-Only User

Create a read-only user for viewing:

**PostgreSQL:**
```sql
CREATE USER readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE your_database TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
```

**MySQL:**
```sql
CREATE USER 'readonly'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT ON your_database.* TO 'readonly'@'%';
FLUSH PRIVILEGES;
```

### 5. Protect Config File

```bash
# Restrict access to config file
chmod 600 backend/dashboard/db_config.json

# Don't commit passwords to git
echo "backend/dashboard/db_config.json" >> .gitignore
```

## Troubleshooting

### Connection Refused

**Problem:** Can't connect to database

**Solutions:**

1. Check if database is running:
   ```bash
   # PostgreSQL
   sudo systemctl status postgresql

   # MySQL
   sudo systemctl status mysql
   ```

2. Verify firewall allows connections:
   ```bash
   sudo ufw status
   ```

3. Test connection manually:
   ```bash
   # PostgreSQL
   psql -h your-droplet-ip -U your_username -d your_database

   # MySQL
   mysql -h your-droplet-ip -u your_username -p your_database
   ```

### Authentication Failed

**Problem:** Wrong username or password

**Solutions:**

1. Reset password:
   ```bash
   # PostgreSQL
   sudo -u postgres psql
   ALTER USER your_username WITH PASSWORD 'new_password';

   # MySQL
   sudo mysql
   ALTER USER 'your_username'@'%' IDENTIFIED BY 'new_password';
   ```

2. Check username exists:
   ```bash
   # PostgreSQL
   sudo -u postgres psql -c "\du"

   # MySQL
   sudo mysql -e "SELECT user, host FROM mysql.user;"
   ```

### No Tables Showing

**Problem:** Connected but no tables appear

**Solutions:**

1. Check user has permissions:
   ```bash
   # PostgreSQL
   sudo -u postgres psql -d your_database -c "\dp"

   # MySQL
   mysql -u your_username -p -e "SHOW GRANTS;"
   ```

2. Verify tables exist:
   ```bash
   # PostgreSQL
   sudo -u postgres psql -d your_database -c "\dt"

   # MySQL
   mysql -u your_username -p your_database -e "SHOW TABLES;"
   ```

### Performance Issues

**Problem:** Slow queries or page loads

**Solutions:**

1. Reduce page size (modify `per_page` in code)
2. Add indexes to frequently queried columns
3. Limit results in custom queries
4. Enable query caching in database

## Architecture

```
ProjectBot/
├── backend/
│   └── dashboard/
│       ├── database_viewer.py      # Flask backend & API
│       ├── db_config.json          # Database connections
│       └── templates/
│           └── database_viewer.html # Frontend UI
├── run_database_viewer.py          # Dashboard launcher
└── requirements.txt                # Dependencies
```

### API Endpoints

- `GET /api/connections` - List all configured connections
- `POST /api/connect` - Connect to a database
- `POST /api/disconnect` - Disconnect from a database
- `GET /api/tables` - Get tables for a connection
- `GET /api/table/schema` - Get schema for a table
- `GET /api/table/data` - Get paginated table data
- `POST /api/query` - Execute custom SELECT query
- `GET /api/export/csv` - Export table to CSV

### Technology Stack

- **Backend:** Python 3.9+, Flask, SQLAlchemy
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Database Drivers:** psycopg2 (PostgreSQL), PyMySQL (MySQL)
- **Data Processing:** Pandas

## Advanced Usage

### Custom Queries Examples

```sql
-- Get recent records
SELECT * FROM orders
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 100;

-- Aggregate data
SELECT
    DATE(created_at) as date,
    COUNT(*) as order_count,
    SUM(total) as revenue
FROM orders
WHERE created_at > '2024-01-01'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Join tables
SELECT
    u.username,
    COUNT(o.id) as order_count,
    SUM(o.total) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username
ORDER BY total_spent DESC
LIMIT 20;
```

### Programmatic Access

You can also use the `DatabaseViewer` class directly in Python:

```python
from backend.dashboard.database_viewer import DatabaseViewer

# Initialize viewer
viewer = DatabaseViewer('backend/dashboard/db_config.json')

# Connect to database
success, message = viewer.connect('Production PostgreSQL')
if success:
    # Get tables
    success, tables, message = viewer.get_tables('Production PostgreSQL')
    for table in tables:
        print(f"{table['name']}: {table['row_count']} rows")

    # Get table data
    success, data, message = viewer.get_table_data(
        'Production PostgreSQL',
        'users',
        page=1,
        per_page=10
    )
    print(data)

    # Execute query
    success, result, message = viewer.execute_query(
        'Production PostgreSQL',
        'SELECT COUNT(*) FROM users'
    )
    print(result)
```

## Integration with Existing Dashboard

If you want to integrate this with the existing Aviator bot dashboard, you can:

1. Add a link in `compact_dashboard.html`:
   ```html
   <a href="http://localhost:5002" target="_blank">Database Viewer</a>
   ```

2. Run both dashboards simultaneously:
   ```bash
   # Terminal 1
   python3 run_dashboard.py

   # Terminal 2
   python3 run_database_viewer.py
   ```

## Future Enhancements

Potential features to add:

- [ ] SSH tunneling support
- [ ] Write operations (INSERT, UPDATE, DELETE) with confirmations
- [ ] Query history and favorites
- [ ] Data visualization (charts from queries)
- [ ] Export to Excel, JSON, Parquet
- [ ] Table comparison tool
- [ ] Database backup/restore UI
- [ ] Multi-database queries
- [ ] Real-time data monitoring
- [ ] User authentication and access control

## Contributing

Feel free to submit issues or pull requests to improve the database viewer.

## License

Part of the ProjectBot Aviator betting bot project.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review database logs on the droplet
3. Check Flask application logs
4. Ensure network connectivity between dashboard and droplet

---

**Happy Database Browsing!** 🗄️
