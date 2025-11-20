# Quick Start: Database Viewer Dashboard

Get the database viewer running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd /home/user/ProjectBot
pip install -r requirements.txt
```

## Step 2: Configure Your Database Connection

Edit `backend/dashboard/db_config.json`:

```json
{
  "connections": [
    {
      "name": "My Database",
      "type": "postgresql",
      "host": "YOUR_DROPLET_IP",
      "port": 5432,
      "database": "YOUR_DATABASE_NAME",
      "username": "YOUR_USERNAME",
      "password": "YOUR_PASSWORD",
      "ssh_tunnel": false,
      "ssh_host": "",
      "ssh_port": 22,
      "ssh_user": "",
      "ssh_key_path": ""
    }
  ]
}
```

Replace:
- `YOUR_DROPLET_IP` with your DigitalOcean droplet IP address
- `YOUR_DATABASE_NAME` with your database name
- `YOUR_USERNAME` with your database username
- `YOUR_PASSWORD` with your database password

For MySQL, change `"type": "postgresql"` to `"type": "mysql"` and `"port": 5432` to `"port": 3306`.

## Step 3: Start the Dashboard

```bash
python3 run_database_viewer.py
```

## Step 4: Access the Dashboard

Open your browser and go to:
```
http://localhost:5002
```

## Step 5: Use the Dashboard

1. **Connect**: Click on your database connection in the left sidebar
2. **Browse Tables**: Click on any table to view its data
3. **View Schema**: Click the "Schema" tab to see table structure
4. **Run Queries**: Click the "Query" tab to execute custom SQL
5. **Export Data**: Click "Export to CSV" to download table data

## Troubleshooting

**Can't connect to database?**
- Make sure your database is running on the droplet
- Verify firewall allows connections on port 5432 (PostgreSQL) or 3306 (MySQL)
- Test connection: `psql -h YOUR_IP -U YOUR_USER -d YOUR_DB` or `mysql -h YOUR_IP -u YOUR_USER -p`

**No tables showing?**
- Check database permissions: `GRANT SELECT ON DATABASE your_db TO your_user;`
- Verify tables exist: `\dt` in psql or `SHOW TABLES;` in MySQL

**Need more help?**
- See [DATABASE_VIEWER_README.md](DATABASE_VIEWER_README.md) for full documentation
- Check database logs on your droplet

---

**That's it! You're ready to explore your database tables.** 🎉
