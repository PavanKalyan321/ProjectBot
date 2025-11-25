# Quick Start: Multi-Browser Data Collection

## 🚀 5-Minute Setup Guide

This guide helps you get 6 browsers running and collecting game data simultaneously.

## Step 1: Open 6 Browser Instances (2 minutes)

### Option A: Single 4K Monitor (Recommended)
```bash
# Double-click this file:
open_6_browsers.bat
```

This opens 6 Chrome instances in incognito mode arranged as:
```
┌──────────────────┬──────────────────┐
│   Browser 0      │   Browser 1      │
│  (0, 0)          │  (1920, 0)       │
├──────────────────┼──────────────────┤
│   Browser 2      │   Browser 3      │
│  (0, 1080)       │  (1920, 1080)    │
├──────────────────┼──────────────────┤
│   Browser 4      │   Browser 5      │
│  (0, 2160)       │  (1920, 2160)    │
└──────────────────┴──────────────────┘
```

### Option B: Dual 4K Monitors
```bash
# Double-click this file:
open_6_browsers_fullscreen.bat

# Choose option 1 when prompted
```

This arranges:
- Left Monitor: Browsers 0, 1, 2 (stacked)
- Right Monitor: Browsers 3, 4, 5 (stacked)

## Step 2: Navigate to Game URL (1 minute)

In each of the 6 browser windows:
1. Go to your game URL
2. Log in to your account
3. Wait for game to fully load

You should see:
- Account balance displayed
- Current multiplier value
- "Place bet" button
- Stake input field
- Player count

## Step 3: Run Data Collector (1 minute)

Open PowerShell and navigate to your project:
```powershell
cd c:\Project
python backend/multi_readregion.py
```

You'll see:
```
🚀 Multi-Browser Data Collector
Choose mode:
1. Setup single browser (interactive validation)
2. Run multi-browser test

Enter choice (1-2): 1
```

## Step 4: Setup Browser 0 (5-15 minutes)

The system will ask:
```
Enter Browser ID (0-5): 0
```

### For Each Data Point:

#### 1️⃣ BALANCE

System will show:
```
📍 DATA POINT 1/5: BALANCE
Description: Player balance/account balance
Data type: float
Example pattern: (\d+\.?\d*)
```

**To find coordinates:**
1. Look at Browser 0 - find where balance is displayed
2. Use Chrome DevTools (F12) to inspect element
3. Right-click > Inspect > measure pixel position from screen top-left

Example answers:
```
Top (pixels from top): 100
Left (pixels from left): 500
Width (pixels): 150
Height (pixels): 40
Enter regex pattern [(\d+\.?\d*)]:
(just press Enter to use default)
```

#### 2️⃣ MULTIPLIER

Find where multiplier displays (usually center of game):
```
Top: 200
Left: 700
Width: 100
Height: 50
```

#### 3️⃣ PLACE_BET

Find the "Place Bet" button:
```
Top: 350
Left: 400
Width: 150
Height: 40
```

#### 4️⃣ STAKE

Find stake/bet amount input:
```
Top: 300
Left: 300
Width: 100
Height: 40
```

#### 5️⃣ PLAYERS

Find player count display:
```
Top: 150
Left: 100
Width: 80
Height: 30
```

### Validation Phase

After entering all coordinates, you'll see:

```
📊 CURRENT VALUES:
────────────────────────────────────────────────────────────
⏳ balance         | Value: 1000.50        | Confidence: 95.0% | Raw: ...
⏳ multiplier      | Value: None           | Confidence: N/A  | Raw: ...
⏳ place_bet       | Value: ACTIVE         | Confidence: 90.0% | Raw: ...
⏳ stake           | Value: 10.00          | Confidence: 95.0% | Raw: ...
⏳ players         | Value: 5              | Confidence: 95.0% | Raw: ...
────────────────────────────────────────────────────────────

Options:
  V<point> - Validate a data point (e.g., 'Vbalance')
  R<point> - Re-enter coordinates
  S       - Show summary
  Q       - Quit and save
```

**Validate working data points:**
```
Enter command: Vbalance
✅ BALANCE validated for Browser 0

Enter command: Vmultiplier
✅ MULTIPLIER validated for Browser 0
```

**If extraction fails (Value: None):**

Use `R` to re-enter coordinates:
```
Enter command: Rmultiplier

Re-entering coordinates for multiplier:
  Top (pixels from top): 180
  Left (pixels from left): 720
  Width (pixels): 120
  Height (pixels): 60
✅ Updated multiplier coordinates
```

**Check progress:**
```
Enter command: S

📋 VALIDATION SUMMARY
────────────────────────────────────────────────────────────
✅ VALIDATED
  Data Point: balance
  Last Value: 1000.50
  Confidence: 95.0%
  Samples: 3

✅ VALIDATED
  Data Point: multiplier
  ...
```

**When all 5 are validated:**
```
Enter command: S

🎉 ALL DATA POINTS VALIDATED!
✅ Configuration saved to browser_0_config.json
```

## Step 5: Repeat for Remaining Browsers

Once Browser 0 is validated:
```
Enter choice (1-2): 1
Enter Browser ID (0-5): 1
```

Repeat the same process for Browsers 2, 3, 4, and 5.

## CSV Logging Starts Immediately

As soon as you enter coordinates, data logging begins!

**Files created:**
- `browser_0_data.csv` - All data from Browser 0
- `browser_1_data.csv` - All data from Browser 1
- ... etc

**Example CSV content:**
```csv
timestamp,browser_id,data_point,value,confidence,raw_ocr,validated
2025-11-20T19:30:45.123456,0,balance,1000.50,0.950,1000.50,True
2025-11-20T19:30:45.234567,0,multiplier,2.34,0.950,2.34,True
2025-11-20T19:30:45.345678,0,place_bet,ACTIVE,0.900,ACTIVE,True
2025-11-20T19:30:45.456789,0,stake,10.00,0.950,10.00,True
2025-11-20T19:30:45.567890,0,players,5,0.950,5,True
```

View logs anytime:
```bash
cat browser_0_data.csv
```

## Coordinate Finding Tips

### Using Chrome DevTools

1. In any browser window, press **F12** to open DevTools
2. Click the element picker icon (top-left, looks like cursor)
3. Click on the element you want to measure
4. Note the pixel position

### Using Python to Test Coordinates

```python
import mss
import numpy as np
from PIL import Image

# Define your region
region = {'top': 100, 'left': 500, 'width': 150, 'height': 40}

# Capture
with mss.mss() as sct:
    img = np.array(sct.grab(region))

# Save screenshot to verify
Image.fromarray(img).save('test_region.png')
print("Saved test_region.png")
```

If the saved image shows the correct data point, your coordinates are right!

## Troubleshooting

### "Value: None" - Not Reading Data

**Problem:** Extract shows None value even though coordinates seem right

**Solution:**
1. Adjust coordinates by ±10 pixels
2. Increase width/height slightly
3. Check if text is actually visible in that area
4. Update regex pattern:
   ```
   Instead of: (\d+\.?\d*)
   Try: (\d+)  (for integers)
   Try: ([\d\.]+)  (more flexible)
   ```

### Low Confidence (< 80%)

**Problem:** Values are extracted but confidence is low

**Solution:**
1. Make capture region larger (increase width/height)
2. Center the region better on the text
3. Make sure the text has good contrast with background

### Browser Not Starting

**Problem:** `open_6_browsers.bat` doesn't work

**Solution:**
```bash
# Check Chrome is installed
dir "C:\Program Files\Google\Chrome\Application\chrome.exe"

# If not found, update path in the .bat file or install Chrome
```

### Pattern Matching Issues

**Test your regex:**
```python
import re

raw_ocr = "Balance: 1000.50"
pattern = r'(\d+\.?\d*)'

match = re.search(pattern, raw_ocr)
if match:
    print(f"Matched: {match.group(1)}")
else:
    print("No match!")
```

## Next: Integration with Betting Logic

Once all 6 browsers are configured and logging:

1. Review CSV data for quality
2. Check confidence scores (aim for > 90%)
3. Integrate `BrowserDataCollector` with your betting logic
4. Use real-time CSV logs for monitoring

```python
from backend.multi_readregion import BrowserDataCollector

# Load your saved config
collector = BrowserDataCollector(browser_id=0)
# ... register data points from your config ...

# Collect continuously
while True:
    results = collector.collect_all_data_points()
    # results = {'balance': (1000.50, 0.95, '1000.50'), ...}

    # Use in your betting logic
    balance, balance_conf, _ = results['balance']
    multiplier, mult_conf, _ = results['multiplier']

    if balance and balance_conf > 0.9:
        # Execute bet logic
        pass
```

## Files Reference

| File | Purpose |
|------|---------|
| `open_6_browsers.bat` | Launch 6 Chrome instances (incognito) |
| `backend/multi_readregion.py` | Data collection system |
| `MULTI_BROWSER_SETUP_GUIDE.md` | Detailed reference guide |
| `browser_0_config.json` | Saved config for Browser 0 (auto-created) |
| `browser_0_data.csv` | CSV logs for Browser 0 (auto-created) |

## Support

- Check `MULTI_BROWSER_SETUP_GUIDE.md` for advanced topics
- Review CSV logs to debug OCR issues
- Use Chrome DevTools (F12) to inspect elements
- Test regex patterns independently

Good luck! 🚀
