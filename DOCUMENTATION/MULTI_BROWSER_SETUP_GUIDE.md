# Multi-Browser Data Collection Setup Guide

## Overview

The `multi_readregion.py` module enables you to collect game data from up to 6 browser instances simultaneously with real-time CSV logging and OCR validation.

### Data Points Collected
1. **Balance** - Player account balance
2. **Multiplier** - Current game multiplier
3. **Place Bet** - Bet placement status/button
4. **Stake** - Bet stake amount
5. **Players** - Number of active players

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Browser System                     │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
      ┌─────▼─────┐     ┌─────▼─────┐    ┌─────▼─────┐
      │ Browser 0 │     │ Browser 1 │    │ Browser 2 │
      │ balance   │     │ balance   │    │ balance   │
      │ multiplier│     │ multiplier│    │ multiplier│
      │ ...       │     │ ...       │    │ ...       │
      └─────┬─────┘     └─────┬─────┘    └─────┬─────┘
            │                 │                 │
      ┌─────▼─────────────────▼─────────────────▼─────┐
      │   Real-time CSV Logging System                │
      │   - browser_0_data.csv                        │
      │   - browser_1_data.csv                        │
      │   - browser_2_data.csv                        │
      └───────────────────────────────────────────────┘
```

## Getting Started

### Step 1: Start Interactive Setup

```bash
python backend/multi_readregion.py
```

Choose option **1** for single browser setup.

### Step 2: Enter Browser ID

```
Enter Browser ID (0-5): 0
```

Choose a browser ID from 0-5. This identifies which browser instance you're configuring.

### Step 3: Configure Data Points

For each of the 5 data points, you'll enter:

#### Example: Balance Configuration

```
📍 DATA POINT 1/5: BALANCE
Description: Player balance/account balance
Data type: float
Example pattern: (\d+\.?\d*)

Enter coordinates for balance:
  Top (pixels from top): 100
  Left (pixels from left): 500
  Width (pixels): 150
  Height (pixels): 40
  Enter regex pattern [(\d+\.?\d*)]:
```

**How to find coordinates:**
1. Open your game in browser 0
2. Look at where the balance is displayed
3. Use browser inspector (F12) to identify exact pixel position
4. Measure width and height of that element

### Step 4: Validation Phase

Once all coordinates are entered, the system enters validation mode:

```
📊 CURRENT VALUES:
────────────────────────────────────────────────────────────
✅ balance         | Value: 1000.50        | Confidence: 95.0% | Raw: ...
⏳ multiplier      | Value: None           | Confidence: N/A  | Raw: ...
⏳ place_bet       | Value: ACTIVE         | Confidence: 90.0% | Raw: ...
⏳ stake           | Value: 10.00          | Confidence: 95.0% | Raw: ...
⏳ players         | Value: 5              | Confidence: 95.0% | Raw: ...
────────────────────────────────────────────────────────────

Options:
  V<point> - Validate a data point (e.g., 'Vbalance', 'Vmultiplier')
  R<point> - Re-enter coordinates for a data point
  S       - Show summary
  Q       - Quit and save
```

### Step 5: Validate Each Data Point

Commands:
- **Vbalance** - Mark balance as validated (working correctly)
- **Vmultiplier** - Mark multiplier as validated
- **Vplace_bet** - Mark bet button as validated
- **Vstake** - Mark stake as validated
- **Vplayers** - Mark players count as validated

If a data point is not being read correctly:
- **Rbalance** - Re-enter balance coordinates
- Adjust the pixel positions slightly and try again

Example validation loop:

```
[Iteration 1]
Vbalance
✅ BALANCE validated for Browser 0

[Iteration 2]
Rmultiplier
Re-entering coordinates for multiplier:
  Top (pixels from top): 120
  Left (pixels from left): 600
  Width (pixels): 100
  Height (pixels): 40
✅ Updated multiplier coordinates

[Iteration 3]
Vmultiplier
✅ MULTIPLIER validated for Browser 0

[Iteration 4]
S  (Show summary)
📋 VALIDATION SUMMARY
────────────────────────────────────────────
✅ VALIDATED
  Data Point: balance
  Last Value: 1000.50
  Confidence: 95.0%
  Samples: 3

✅ VALIDATED
  Data Point: multiplier
  Last Value: 2.34
  Confidence: 95.0%
  Samples: 3

⏳ PENDING
  Data Point: place_bet
  Last Value: ACTIVE
  Confidence: 90.0%
  Samples: 3
```

### Step 6: All Data Points Validated

Once all 5 data points are validated:

```
🎉 ALL DATA POINTS VALIDATED!
✅ Configuration saved to browser_0_config.json
```

## Real-Time CSV Logging

After validation starts, each data point is logged in real-time to:

**File:** `browser_0_data.csv` (for browser 0)

**Structure:**
```csv
timestamp,browser_id,data_point,value,confidence,raw_ocr,validated
2025-11-20T19:30:45.123456,0,balance,1000.50,0.950,1000.50,True
2025-11-20T19:30:45.234567,0,multiplier,2.34,0.950,2.34x,True
2025-11-20T19:30:45.345678,0,place_bet,ACTIVE,0.900,ACTIVE,True
2025-11-20T19:30:45.456789,0,stake,10.00,0.950,10.00,True
2025-11-20T19:30:45.567890,0,players,5,0.950,5,True
```

### CSV Columns Explained

| Column | Description | Example |
|--------|-------------|---------|
| timestamp | When data was collected | 2025-11-20T19:30:45.123456 |
| browser_id | Which browser instance | 0 |
| data_point | Which data point | balance, multiplier, etc |
| value | Extracted and converted value | 1000.50 |
| confidence | OCR confidence (0-1) | 0.950 |
| raw_ocr | Raw text from OCR | 1000.50 |
| validated | User validation status | True |

## Regex Patterns Reference

### Common Patterns

**Currency/Balance (floats):**
```regex
(\d+\.?\d*)        # Matches: 1000, 1000.5, 1000.50
(\d+\.\d{2})       # Matches: 1000.50 (always 2 decimals)
```

**Multiplier (decimal format):**
```regex
(\d+\.\d+)         # Matches: 2.34, 10.5, 100.99
x(\d+\.\d+)        # Matches: x2.34 (with x prefix)
```

**Button Status (strings):**
```regex
(PLACE|BET|ACTIVE|INACTIVE)      # Any of these
(AWAITING|FLYING|CRASHED)         # Game states
```

**Integer Count:**
```regex
(\d+)              # Matches: 1, 5, 100, 9999
Players:\s*(\d+)   # Matches: "Players: 5"
```

## Troubleshooting

### OCR Not Reading Values

**Issue:** Confidence is 0%, value is None

**Solutions:**
1. Verify coordinates are exactly where the text appears
2. Try adjusting width/height by ±10 pixels
3. Update regex pattern to match the actual text format
4. Check if the text color contrasts well with background

### Confidence Too Low (< 80%)

**Issue:** Values are extracted but confidence is 0.7 or lower

**Solutions:**
1. Make the region capture area larger (increase width/height)
2. Adjust the top/left coordinates to better center the text
3. Modify the regex pattern to be more flexible
4. The text might be in a different format than expected

### Pattern Not Matching

**Test your regex:**
```python
import re
raw_ocr = "Balance: 1000.50"
pattern = r'(\d+\.?\d*)'
match = re.search(pattern, raw_ocr)
print(match.group(1) if match else "No match")
```

## Advanced Usage

### Python API

```python
from backend.multi_readregion import BrowserDataCollector

# Create collector for browser 0
collector = BrowserDataCollector(browser_id=0, enable_realtime_logging=True)

# Register data points
collector.register_data_point(
    'balance',
    region={'top': 100, 'left': 500, 'width': 150, 'height': 40},
    pattern=r'(\d+\.?\d*)',
    data_type='float'
)

# Collect all data
results = collector.collect_all_data_points()
# Returns: {'balance': (1000.50, 0.95, '1000.50'), ...}

# Get current state
state = collector.get_current_state()

# Get validation report
report = collector.get_validation_report()
# Returns metrics and log file location

# Close logger
collector.close_logger()
```

### Multi-Browser Collection

```python
from backend.multi_readregion import MultiScreenMultiplierReader

# Define regions for 6 browsers
browser_regions = {
    0: {"top": 506, "left": 330, "width": 322, "height": 76},
    1: {"top": 506, "left": 680, "width": 322, "height": 76},
    # ... etc
}

# Create reader
reader = MultiScreenMultiplierReader(browser_regions)

# Read all browsers simultaneously
results = reader.read_all_browsers()
# Returns: {0: 2.34, 1: 1.56, 2: 3.21, ...}

# Get status of all browsers
statuses = reader.get_all_statuses()

# Get OCR validation report
report = reader.get_ocr_validation_report()
```

## Configuration Files

After validation, a config file is created:

**File:** `browser_0_config.json`

```json
{
  "browser_id": 0,
  "data_points": {
    "balance": {
      "region": {"top": 100, "left": 500, "width": 150, "height": 40},
      "pattern": "(\\d+\\.?\\d*)",
      "data_type": "float",
      "validated": true
    },
    "multiplier": {
      "region": {"top": 120, "left": 600, "width": 100, "height": 40},
      "pattern": "(\\d+\\.\\d+)",
      "data_type": "float",
      "validated": true
    },
    ...
  },
  "timestamp": "2025-11-20T19:30:45.123456"
}
```

You can reload this configuration later instead of re-entering coordinates.

## Performance Tips

1. **Parallel Collection:** Use threading for multiple browsers (automatically done)
2. **Confidence Threshold:** Monitor confidence scores; aim for > 90%
3. **CSV I/O:** Logs are flushed immediately; no data loss on crash
4. **Screen Resolution:** Works best at native resolution (don't scale)
5. **Update Frequency:** Default 0.03s between reads; adjust if needed

## Next Steps

1. ✅ Set up Browser 0 with all 5 data points
2. Repeat for Browsers 1-5 (one by one)
3. Review CSV logs for data quality
4. Use configuration files for production runs
5. Integrate with your betting logic

## Support

If data is not being captured correctly:
1. Check the CSV log file for raw OCR output
2. Verify regex patterns against raw OCR text
3. Adjust coordinates and confidence thresholds
4. Use browser developer tools (F12) to inspect element positions

Good luck with your multi-browser setup! 🚀
