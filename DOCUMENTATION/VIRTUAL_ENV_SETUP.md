# Python Virtual Environment Setup

Isolate your Aviator Bot project from other Python projects on your laptop.

## What is a Virtual Environment?

A virtual environment is a self-contained Python installation for this project:
- **Isolated dependencies** - Only packages for THIS project are installed
- **No conflicts** - Other projects won't interfere with this one
- **Clean system** - Your system Python stays untouched
- **Easy cleanup** - Delete folder to remove everything

## Current Status

Your project is located at: `c:\Project\`

## Setup Instructions

### Step 1: Create Virtual Environment

Open Command Prompt or PowerShell in `c:\Project\` and run:

**Windows (Command Prompt):**
```bash
python -m venv venv
```

**Windows (PowerShell):**
```powershell
python -m venv venv
```

This creates a `venv` folder (~200MB) with isolated Python.

### Step 2: Activate Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Expected Output:**
```
(venv) c:\Project>
```

Notice `(venv)` at the start - this means the virtual environment is active.

### Step 3: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 4: Install Project Dependencies

```bash
pip install -r requirements.txt
```

This installs ALL required packages in the isolated environment:
- flask, flask-socketio
- pandas, numpy, scikit-learn
- tensorflow, lightgbm
- sqlalchemy, psycopg2-binary
- python-dotenv
- And 20+ more packages

**Expected Time:** 5-15 minutes (depending on internet speed)

### Step 5: Verify Installation

```bash
python verify_supabase_setup.py
```

Expected output: `✓ ALL CHECKS PASSED`

## Using the Virtual Environment

### Every Time You Work on This Project

**Before running any Python scripts:**

**Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal.

### Running Your Bot/Dashboard

With virtual environment active:

```bash
# Run the bot
python backend/bot.py --mode dry_run

# Run the dashboard
python run_dashboard.py

# Run migration script
python migrate_to_supabase.py
```

### Deactivate Virtual Environment

When you're done:

```bash
deactivate
```

The `(venv)` prefix disappears from your terminal.

## Project Structure with Virtual Environment

```
c:\Project\
├── venv/                          ← Virtual environment folder
│   ├── Scripts/                   ← Python executables
│   │   ├── python.exe
│   │   ├── pip.exe
│   │   └── activate.bat
│   ├── Lib/                       ← Installed packages
│   │   └── site-packages/
│   └── pyvenv.cfg                 ← Configuration
│
├── .env                           ← Supabase credentials
├── requirements.txt               ← Dependencies list
├── venv.pth                       ← Path file (auto-generated)
│
├── backend/
│   ├── database/
│   │   └── ... (database files)
│   ├── bot.py
│   └── dashboard/
│
└── ... (other project files)
```

## Managing Virtual Environment

### Add New Package

With virtual environment active:

```bash
pip install package_name
```

Then update requirements.txt:

```bash
pip freeze > requirements.txt
```

### Remove Package

```bash
pip uninstall package_name
```

### List Installed Packages

```bash
pip list
```

### See Virtual Environment Info

```bash
pip show package_name
```

## Protect Virtual Environment

Update `.gitignore` to exclude the venv folder (already done if you followed earlier setup):

```
venv/
.venv/
env/
ENV/
```

The virtual environment should NEVER be committed to git - it's large (~200MB) and platform-specific.

## Troubleshooting

### Issue: "venv is not recognized"

**Solution:** You're not in the `c:\Project\` folder. Navigate there first:
```bash
cd c:\Project
venv\Scripts\activate.bat
```

### Issue: "Python is not recognized"

**Solution:** Python is not in PATH. Install it from python.org or use:
```bash
python -m venv venv
```

### Issue: "Permission denied" (PowerShell)

**Solution:** Run PowerShell as Administrator, or:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "cannot find pip"

**Solution:** Ensure you activated the virtual environment:
```bash
venv\Scripts\activate.bat
pip list
```

### Issue: Packages installed but not found

**Solution:** Make sure virtual environment is active (check for `(venv)` prefix)

## Multiple Projects on Same Laptop

### Project 1: Aviator Bot (THIS PROJECT)
```
c:\Project\
├── venv\                  ← ISOLATED to this project
└── ... files
```

### Project 2: Some Other Project
```
c:\SomeOtherProject\
├── venv\                  ← SEPARATE - doesn't interfere
└── ... files
```

Each project has its OWN `venv` folder with its OWN packages. They never conflict!

## Benefits of Virtual Environment

✓ **Isolation** - This project's packages don't affect others
✓ **Reproducibility** - requirements.txt lists exact versions
✓ **Clean System** - System Python stays clean
✓ **Easy Setup** - New team member runs `pip install -r requirements.txt`
✓ **Easy Reset** - Delete `venv/` folder to start fresh

## Complete Workflow

```bash
# 1. Navigate to project
cd c:\Project

# 2. Activate virtual environment
venv\Scripts\activate.bat

# 3. You should see: (venv) c:\Project>

# 4. Install dependencies (one time)
pip install -r requirements.txt

# 5. Create schema in Supabase (one time, in browser)

# 6. Run your bot/dashboard
python backend/bot.py --mode dry_run

# 7. When done, deactivate
deactivate
```

## Important Notes

1. **Always activate before running Python**
   - Without activation, your system Python is used
   - With activation, isolated Python is used

2. **Virtual environment is one-time setup**
   - Create it once: `python -m venv venv`
   - Activate it every time you work
   - Delete it if you want to start fresh

3. **requirements.txt is your dependency list**
   - This file lives in the project (not in venv)
   - It's committed to git for reproducibility
   - New developers run: `pip install -r requirements.txt`

4. **venv folder should be in .gitignore**
   - It's large (~200MB) and platform-specific
   - Never commit it to git

## VS Code Integration (Optional)

If using VS Code, it can auto-detect your virtual environment:

1. Open VS Code in `c:\Project\`
2. Press `Ctrl + Shift + P`
3. Type: "Python: Select Interpreter"
4. Choose: `./venv/Scripts/python.exe`

VS Code will automatically activate the venv when you open the terminal!

## Next Steps

1. **Create virtual environment:**
   ```bash
   cd c:\Project
   python -m venv venv
   ```

2. **Activate it:**
   ```bash
   venv\Scripts\activate.bat
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify setup:**
   ```bash
   python verify_supabase_setup.py
   ```

5. **You're ready to go!**

---

Your project is now completely isolated from other Python projects on your laptop!
