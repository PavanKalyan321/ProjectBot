# Quick Start: Iframe DOM Scanner

## What It Does
Continuously monitors your iframe for **10 seconds** and identifies ALL multiplier elements with exact selectors (XPath, CSS selector, attributes).

## Quick Steps

### 1. Open Dashboard
Navigate to your dashboard with the iframe loaded.

### 2. Click "Scanner" Button
In the right panel (where Event Log is), click the **"Scanner"** button to switch views.

### 3. Click "Start 10s Scan"
Blue button at the top. The scan will run for exactly 10 seconds.

### 4. Watch Live Updates
See real-time progress:
```
Elements Found: 145
Multiplier Elements: 3
Numeric Patterns: 8
Values: 2.45x, 2.50x, 2.55x
```

### 5. Review Results
After 10 seconds:
- **Most Reliable Multiplier**: Shows the value that appeared most
- **Scan Report**: Detailed element information

### 6. Export Data
- Click **"Export JSON"** for raw data
- Click **"Export Report"** for readable text

## What You'll Find

### XPath Examples
```
Single digit location:
//*[@id="root"]/div[1]/div[3]/div[2]/div[2]

Multi-digit locations:
//*[@id="root"]/div[1]/div[3]/div[2]/div[3]
//*[@id="game-stats"]/div[2]/span[1]
//div[@data-value="2.45"]
```

### CSS Selectors
```
#root > div > div:nth-child(3) > div:nth-child(2) > div:nth-child(2)
.game-multiplier.active
[data-value="2.45"]
```

### Element Info
```
Tag: div
ID: multiplier-value
Class: game-multiplier active
Text: "2.45"
Attributes: {"data-value":"2.45"}
```

## Use Cases

### 1. Discover All Multiplier Locations
```
Run scan → Review report → Copy all XPaths found
```

### 2. Handle Variable Digit Counts
```
Game shows 1-3 digits? Scanner finds all locations
Try each location in extraction loop
```

### 3. Switch Between Game Variants
```
Different platform? Run scanner on each
Compare XPaths between platforms
Update extraction logic accordingly
```

### 4. Debug Extraction Issues
```
Extraction failing? Run scanner to verify element exists
Check if XPath matches actual element
Export JSON for detailed analysis
```

## Key Information Captured

For each multiplier element found:
- ✅ Full tag name
- ✅ ID and CSS classes
- ✅ Exact text content
- ✅ XPath selector
- ✅ CSS selector
- ✅ All HTML attributes
- ✅ Complete HTML snippet

## Most Reliable Multiplier

The scanner shows:
```
Value: 2.45x
Frequency: 12 occurrences
Confidence: 85%
```

This means:
- The value **2.45** was found in 12 different scans
- Out of 20 total scans (10 seconds × 2 per second)
- High confidence it's the actual multiplier

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No elements found | Wait for iframe to load fully (check "Connected" status) |
| Few multiplier elements | Start scan while game is actively running |
| Different values | Normal! Check "Most Reliable Multiplier" for consensus |
| Can't export | Make sure scan completed (10 seconds) |

## Integration Tips

### Once You Have XPaths
Update your extraction code:

```typescript
// Before: Only single location
const MULTIPLIER_XPATH = '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]';

// After: Multiple locations from scanner
const MULTIPLIER_XPATHS = [
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]',    // From scan #1
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[3]',    // From scan #5
  '//*[@id="game-stats"]/div[2]/span[1]',           // From scan #15
];

// Try each until one works
for (const xpath of MULTIPLIER_XPATHS) {
  const result = await extractMultiplierViaXPath(iframeRef, xpath);
  if (result.multiplier) return result;
}
```

## File Locations

- **Scanner Utility**: `src/lib/iframe-dom-scanner.ts`
- **Scanner Component**: `src/components/IframeDOMScanner.tsx`
- **Integration**: `src/components/LeftIframe.tsx`
- **Full Guide**: `DOM_SCANNER_GUIDE.md`

## Export Formats

### JSON Export
```json
[
  {
    "timestamp": "2025-11-25T10:30:45.123Z",
    "elements": [...],
    "multiplierElements": [...],
    "numericPatterns": [
      {
        "element": {...},
        "value": 2.45,
        "format": "2.45 (decimal)"
      }
    ]
  }
]
```

### Text Report
```
=== IFRAME DOM SCAN REPORT ===
Total Scans: 20
Duration: 10.0 seconds

=== IDENTIFIED MULTIPLIER ELEMENTS (5) ===
Tag: <div>
ID: multiplier-value
XPath: //*[@id="root"]/div[1]/div[3]/div[2]/div[2]
...
```

## Key Metrics

- **Scan Duration**: Exactly 10 seconds
- **Scan Frequency**: Every 500ms (20 scans total)
- **Elements Scanned**: All elements in iframe DOM
- **Memory Usage**: Minimal
- **Browser Performance**: No impact

---

**Next Step**: Run a scan and export results to identify all your multiplier element locations!
