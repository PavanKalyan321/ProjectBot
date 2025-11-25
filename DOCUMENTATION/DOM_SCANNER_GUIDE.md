# Iframe DOM Scanner - Complete Guide

## Overview

The **Iframe DOM Scanner** is a comprehensive tool that continuously captures and analyzes the DOM structure of your iframe for **10 seconds**, identifying all multiplier-related elements and their exact selectors (XPath, CSS selector, attributes).

This solves the problem of having only a single-digit XPath by automatically discovering all multiplier elements across different formats and digit counts.

## Features

### 1. **Continuous DOM Capture**
- Scans iframe every 500ms for 10 seconds
- Captures all DOM elements with text content
- Filters out noise (script, style tags, empty elements)

### 2. **Element Identification**
- Detects multiplier-related elements by keywords
- Identifies numeric patterns in various formats:
  - Decimal format: `1.23`, `5.67`
  - With symbols: `1.23x`, `5.67×`
  - Plain numbers: `1`, `23`, `456`

### 3. **Detailed Element Analysis**
Each identified element includes:
- **Tag**: HTML element type (div, span, p, etc.)
- **ID**: Element ID attribute
- **Class**: CSS classes
- **Text**: Content of the element
- **XPath**: Full XPath selector
- **CSS Selector**: CSS selector path
- **Attributes**: All HTML attributes

### 4. **Real-Time Monitoring**
Shows live updates during the 10-second scan:
- Elements found count
- Multiplier elements detected
- Numeric patterns discovered
- Values in real-time

### 5. **Comprehensive Reporting**
Generates detailed reports including:
- All identified multiplier elements with selectors
- Numeric patterns found and their locations
- Timeline of each scan update
- Most reliable multiplier value and frequency

### 6. **Data Export**
Export scan results in two formats:
- **JSON**: Complete raw data for programmatic use
- **Text Report**: Human-readable format with analysis

## How to Use

### Step 1: Access the Scanner
In the LeftIframe component, click the **"Scanner"** button in the top-right of the right panel to switch from Event Log to DOM Scanner.

### Step 2: Start the Scan
Click **"Start 10s Scan"** button to begin the continuous DOM capture.

### Step 3: Monitor Live Updates
Watch the live updates as they come in:
- Number of elements found
- Multiplier elements detected
- Numeric values discovered

### Step 4: Review Results
After 10 seconds, the scan completes and shows:
- **Most Reliable Multiplier**: The value that appeared most frequently
- **Confidence**: How confident the system is in that value
- **Scan Report**: Detailed analysis of all elements found

### Step 5: Export Data
Export the scan results:
- **Export JSON**: Save raw data for debugging or further analysis
- **Export Report**: Save human-readable report

## Understanding the Report

### Example Report Structure

```
=== IFRAME DOM SCAN REPORT ===

Total Scans: 20
Duration: 10.0 seconds

=== IDENTIFIED MULTIPLIER ELEMENTS (5) ===

Tag: <div>
ID: multiplier-value
Class: game-multiplier active
Text: "2.45"
XPath: //*[@id="root"]/div[1]/div[3]/div[2]/div[2]
CSS Selector: #root > div > div:nth-child(3) > div:nth-child(2) > div:nth-child(2)
Attributes: {"data-value":"2.45","class":"game-multiplier active"}

=== NUMERIC PATTERNS FOUND (15) ===

Multiplier: 2.45x
  Found in 8 location(s):
    - //*[@id="root"]/div[1]/div[3]/div[2]/div[2] (2.45 with x/×)
    - //*[@id="game-stats"]/div/span[1] (2.45 (decimal))

Multiplier: 2.50x
  Found in 4 location(s):
    ...

=== SCAN TIMELINE ===

[0] 2025-11-25T10:30:45.123Z
  Elements: 145
  Multiplier Elements: 3
  Numeric Patterns: 5
  Values: 2.45x, 2.50x

[1] 2025-11-25T10:30:45.623Z
  Elements: 145
  Multiplier Elements: 3
  Numeric Patterns: 5
  Values: 2.50x, 2.55x
```

## XPath Discovery Patterns

The scanner identifies elements using multiple XPath patterns:

### Single Element XPath (ID-based)
```
//*[@id="root"]/div[1]/div[3]/div[2]/div[2]
```

### Multi-digit or Alternative Locations
```
//*[@id="game-stats"]/div[2]/span[1]
//*[contains(@class, "multiplier")]/text()
//div[@data-value="2.45"]
//*[@id="root"]/div[1]/div[3]/div[2]/div[3]  // Different digit count
```

## Integration with Extraction System

### Using Discovered XPaths

Once you've identified all possible XPath locations, you can update the extraction system:

```typescript
// Original - only single digit location
const result = await extractMultiplierViaXPath(
  iframeRef,
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]'
);

// Enhanced - try multiple locations
const locations = [
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]',      // Single digit
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[3]',      // Double digit
  '//*[@id="game-stats"]/div[2]/span[1]',              // Alternative
];

for (const xpath of locations) {
  const result = await extractMultiplierViaXPath(iframeRef, xpath);
  if (result.multiplier !== null) return result;
}
```

### Updating the Continuous Extraction

Modify the LeftIframe component's XPath extraction hook:

```typescript
// Enhanced with multiple XPath locations
const MULTIPLIER_XPATHS = [
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]',
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[3]',
  '//*[@id="game-stats"]/div[2]/span[1]',
];

useEffect(() => {
  const extractInterval = setInterval(async () => {
    for (const xpath of MULTIPLIER_XPATHS) {
      const result = await extractMultiplierViaXPath(iframeRef, xpath);
      if (result.multiplier !== null) {
        // Use this result
        break;
      }
    }
  }, 500);

  return () => clearInterval(extractInterval);
}, [isIframeLoaded, status]);
```

## Troubleshooting

### Scanner Finds No Elements
- **Cause**: Iframe content not loaded
- **Solution**: Start scan after iframe is fully loaded (wait for "Connected" status)

### Few Multiplier Elements Found
- **Cause**: Game is not actively running/updating
- **Solution**: Start scan while the game is in play

### Unexpected Values in Pattern
- **Cause**: Regex matching other numeric content
- **Solution**: Filter by value range in extraction (0 < value < 10000)

### Different Values Across Updates
- **Cause**: Game multiplier is changing during scan
- **Solution**: This is normal! Check "Most Reliable Multiplier" for the most frequent value

## Technical Details

### Scan Algorithm

1. **Extract Elements**: Walk entire iframe DOM tree
2. **Filter**: Keep only elements with text content
3. **Identify Multipliers**: Match keywords and numeric patterns
4. **Extract Patterns**: Find all numeric formats (1.23, 1.23x, etc.)
5. **Track Frequency**: Monitor value changes across 10-second window
6. **Analyze**: Generate report with statistics

### Performance

- **Scan Interval**: 500ms (20 scans in 10 seconds)
- **DOM Walk Time**: <50ms per scan
- **Memory Usage**: Minimal (results only stored in memory)
- **Browser Impact**: Negligible

## Advanced Usage

### Custom Scan Duration
```typescript
const results = await startContinuousDOMScan(iframeRef, 5); // 5 seconds
```

### Programmatic Access to Results
```typescript
const results = await startContinuousDOMScan(iframeRef, 10, (update) => {
  console.log('Live update:', update.numericPatterns);
});

const reliable = getMostReliableMultiplier(results);
console.log(`Most common: ${reliable.value.toFixed(2)}x`);
```

### Export Specific Data
```typescript
import { exportScanResults, generateScanReport } from '@/lib/iframe-dom-scanner';

const json = exportScanResults(results);
const report = generateScanReport(results);
```

## Best Practices

1. **Wait for Iframe Load**: Always start scan after "Connected" status
2. **Multiple Scans**: Run multiple scans to identify stable XPaths
3. **Different Game States**: Scan when game is awaiting, running, and crashed
4. **Document Findings**: Export reports for each game/platform variant
5. **Update Extraction**: Periodically update extraction logic with new XPaths found

## Files Modified

### New Files Created
- `src/lib/iframe-dom-scanner.ts` - Core scanner utility
- `src/components/IframeDOMScanner.tsx` - UI component

### Files Updated
- `src/components/LeftIframe.tsx` - Added scanner integration

## API Reference

### `startContinuousDOMScan(iframeRef, durationSeconds, onUpdate?): Promise<ScanResult[]>`
Runs continuous scan for specified duration.

### `generateScanReport(results): string`
Creates human-readable report from scan results.

### `getMostReliableMultiplier(results): { value, confidence, frequency }`
Analyzes results to find most stable multiplier value.

### `exportScanResults(results): string`
Exports raw results as JSON string.

## Examples

### Example 1: Quick Scan and Export
```typescript
const results = await startContinuousDOMScan(iframeRef, 10);
const report = generateScanReport(results);
console.log(report); // Print to console
```

### Example 2: Find Multiplier with Highest Frequency
```typescript
const reliable = getMostReliableMultiplier(results);
console.log(`Use XPath for value: ${reliable.value}x`);
console.log(`Found ${reliable.frequency} times`);
```

### Example 3: Get All XPaths for a Specific Value
```typescript
results.forEach(result => {
  result.numericPatterns
    .filter(p => p.value === 2.45)
    .forEach(p => console.log(p.element.xpath));
});
```

---

**Last Updated**: 2025-11-25
**Version**: 1.0
