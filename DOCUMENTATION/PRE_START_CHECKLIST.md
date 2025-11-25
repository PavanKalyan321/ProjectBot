# ✅ Pre-Start Checklist

Before you start the system, verify everything is in place:

## Environment Setup

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Virtual environment created (if using one)
- [ ] Dependencies installed:
  ```bash
  pip install flask flask-socketio sqlalchemy psycopg2-binary
  cd dashboard-nextjs && npm install
  ```

## Database Configuration

- [ ] `.env` file exists with database credentials
- [ ] Database host is accessible
- [ ] Database user has correct permissions
- [ ] Tables created (analytics_round_multipliers, crash_game_rounds)
- [ ] No database connection errors

## Ports Available

- [ ] Port 5001 is available (backend)
- [ ] Port 3000 is available (frontend)
- [ ] Check: `netstat -ano | findstr :5001` (Windows) or `lsof -i :5001` (Mac/Linux)

## Project Structure

- [ ] `/backend` directory exists
  - [ ] `run_dashboard.py` exists
  - [ ] `dashboard/` folder exists
  - [ ] `database/` folder exists
  
- [ ] `/dashboard-nextjs` directory exists
  - [ ] `src/` folder exists
  - [ ] `src/components/` has Dashboard.tsx and LeftIframe.tsx
  - [ ] `src/lib/` has api.ts and iframe-extractor.ts
  - [ ] `package.json` exists

- [ ] Documentation files exist
  - [ ] `README_IFRAME_EXTRACTION.md`
  - [ ] `START_HERE.md`
  - [ ] `INTEGRATION_SUMMARY.md`

## Code Integration

- [ ] Dashboard.tsx has extractMultiplier import (line 8)
- [ ] Dashboard.tsx has leftIframeRef defined (line 30)
- [ ] Dashboard.tsx has extraction effect (line 248+)
- [ ] Dashboard.tsx passes ref to LeftIframe (line 395)
- [ ] iframe-extractor.ts is at src/lib/iframe-extractor.ts
- [ ] api.ts has logMultiplier and createRound functions

## Backend Readiness

- [ ] multiplier_logger.py exists (backend/database/)
- [ ] multiplier_api.py exists (backend/dashboard/)
- [ ] Both files import correctly
- [ ] Database connection test passes

## Frontend Readiness

- [ ] No TypeScript errors in Dashboard.tsx
- [ ] No missing imports
- [ ] Development server can start without errors
- [ ] Hot reload works correctly

## Quick Verification Commands

```bash
# Check backend file
ls -la backend/database/multiplier_logger.py
ls -la backend/dashboard/multiplier_api.py

# Check frontend files
ls -la dashboard-nextjs/src/lib/iframe-extractor.ts
ls -la dashboard-nextjs/src/lib/api.ts
ls -la dashboard-nextjs/src/components/Dashboard.tsx

# Check ports
lsof -i :5001  # Port 5001
lsof -i :3000  # Port 3000

# Check Python/Node versions
python --version
node --version
npm --version
```

## You're Ready If

✅ All checkboxes above are checked
✅ No error messages in terminal
✅ Ports 3000 and 5001 are available
✅ Database credentials are configured
✅ All required files exist

## If Something is Missing

### Missing database files?
```bash
# Check if tables exist
psql your_database -c "\dt analytics_round_multipliers"
```

### Missing Python dependencies?
```bash
pip install flask flask-socketio sqlalchemy psycopg2-binary python-dotenv
```

### Missing Node dependencies?
```bash
cd dashboard-nextjs
npm install
npm install lucide-react recharts
```

### TypeScript errors?
```bash
cd dashboard-nextjs
npm run build
# Check error messages
```

## Ready to Start?

Once all checkboxes are complete, proceed with:

```bash
# Terminal 1
cd c:\Project
python run_dashboard.py --port 5001

# Terminal 2
cd c:\Project\dashboard-nextjs
npm run dev

# Browser
http://localhost:3000
```

Then enable Demo Mode and watch extraction in console (F12).

---

**Note:** If you encounter ANY errors during startup, check this list again and ensure all prerequisites are met.
