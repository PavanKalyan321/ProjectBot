# Iframe Multiplier Extraction Guide

## Overview

The iframe multiplier extraction system provides **multiple methods to extract the exact multiplier value** displayed in the Aviator game iframe in real-time.

## What Was Created

**New File:** `src/lib/iframe-extractor.ts`

This module provides several extraction methods:

### 1. **PostMessage Method** (Most Reliable)
```typescript
extractMultiplierViaPostMessage(iframeRef)
```
- Communicates with iframe via Window.postMessage API
- Requires iframe to implement message listener
- Most reliable if iframe supports it
- Returns: `{ multiplier: 1.23, method: "postmessage", confidence: 0.95 }`

### 2. **Regex Pattern Matching** (Fallback)
```typescript
extractMultiplierViaRegex(iframeRef)
```
- Searches iframe DOM for multiplier text patterns
- Looks for patterns like "1.23x", "multiplier: 1.23", etc.
- Works without special iframe support
- Returns: `{ multiplier: 1.23, method: "regex", confidence: 0.85 }`

### 3. **API Call Method** (Direct Backend)
```typescript
extractMultiplierViaAPI(sessionId)
```
- Calls game backend API directly
- Gets server-side current multiplier state
- Most accurate but requires API endpoint
- Returns: `{ multiplier: 1.23, method: "api", confidence: 0.99 }`

### 4. **OCR Method** (Advanced)
```typescript
extractMultiplierViaOCR(iframeRef)
```
- Uses Optical Character Recognition on canvas
- Highest accuracy but requires Tesseract.js library
- Can extract from game graphics directly
- Falls back to regex if OCR not available

### 5. **Auto Method** (Best of All)
```typescript
extractMultiplier(iframeRef, "auto")
```
- Tries all methods in order of reliability
- Returns first successful result
- Falls back gracefully if methods fail
- Perfect for production use

## Usage Examples

### Simple Extraction (One-Time)

```typescript
import { extractMultiplier } from "@/lib/iframe-extractor";

// In your component
const iframeRef = useRef<HTMLIFrameElement>(null);

// Extract multiplier once
const result = await extractMultiplier(iframeRef);
console.log(`Multiplier: ${result.multiplier}x`);
console.log(`Method: ${result.method}`);
console.log(`Confidence: ${result.confidence}`);
```

### Continuous Extraction (Real-Time Tracking)

```typescript
import { startContinuousExtraction } from "@/lib/iframe-extractor";

useEffect(() => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Start continuous extraction
  const stopExtraction = startContinuousExtraction(
    iframeRef,
    (result) => {
      // This callback runs whenever multiplier changes
      if (result.multiplier) {
        console.log(`🎮 Multiplier: ${result.multiplier}x`);
        console.log(`📊 Method: ${result.method}`);
        console.log(`✅ Confidence: ${result.confidence * 100}%`);

        // Update state, log to database, etc.
        setLiveData(prev => ({
          ...prev,
          multiplier: result.multiplier,
          extractionMethod: result.method,
          confidence: result.confidence
        }));
      }
    },
    500  // Extract every 500ms
  );

  // Cleanup
  return () => stopExtraction();
}, []);
```

### Specific Method Selection

```typescript
// Use only PostMessage
const result = await extractMultiplier(iframeRef, "postmessage");

// Use only Regex (fastest)
const result = await extractMultiplier(iframeRef, "regex");

// Use only API (most accurate)
const result = await extractMultiplier(iframeRef, "api");
```

## Return Type

Every extraction function returns a `MultiplierExtractionResult`:

```typescript
interface MultiplierExtractionResult {
  multiplier: number | null;        // The extracted multiplier (e.g., 1.23)
  method: "ocr" | "regex" | "api" | "postmessage" | "state" | "failed";
  confidence: number;               // 0-1 (how confident we are)
  rawValue?: string;                // Original text before parsing
  timestamp: string;                // ISO timestamp of extraction
  error?: string;                   // Error message if failed
}
```

### Example Response

```javascript
{
  multiplier: 1.89,
  method: "regex",
  confidence: 0.85,
  rawValue: "1.89x",
  timestamp: "2025-11-25T12:34:56.789Z",
  error: null
}
```

## Integration with Dashboard

### Step 1: Add ref to LeftIframe Component

Modify `LeftIframe.tsx` to expose iframe ref:

```typescript
import { forwardRef } from "react";

export interface LeftIframeHandle {
  getIframeRef: () => React.RefObject<HTMLIFrameElement>;
}

const LeftIframe = forwardRef<LeftIframeHandle, LeftIframeProps>(
  ({ multiplier, status, ... }, ref) => {
    const iframeRef = useRef<HTMLIFrameElement>(null);

    useImperativeHandle(ref, () => ({
      getIframeRef: () => iframeRef
    }));

    return (
      // ... your component
    );
  }
);

export default LeftIframe;
```

### Step 2: Use in Dashboard

```typescript
import { extractMultiplier, startContinuousExtraction } from "@/lib/iframe-extractor";

export default function Dashboard() {
  const leftIframeRef = useRef<any>(null);

  // Enable iframe multiplier extraction
  useEffect(() => {
    if (!leftIframeRef.current) return;

    const iframeRef = leftIframeRef.current.getIframeRef();

    const stopExtraction = startContinuousExtraction(
      iframeRef,
      async (result) => {
        if (result.multiplier && result.confidence > 0.7) {
          // Update local state
          setLiveData(prev => ({
            ...prev,
            multiplier: result.multiplier,
            extractionMethod: result.method
          }));

          // Log to database
          if (currentRoundId) {
            await logMultiplier({
              bot_id: BOT_ID,
              multiplier: result.multiplier,
              round_id: currentRoundId,
              ocr_confidence: result.confidence,
              timestamp: result.timestamp
            });
          }
        }
      },
      500  // Check every 500ms
    );

    return () => stopExtraction();
  }, []);

  return (
    <LeftIframe ref={leftIframeRef} ... />
  );
}
```

## How Each Method Works

### PostMessage Flow
```
Dashboard Component
     ↓
Send: { type: "GET_MULTIPLIER" }
     ↓
Iframe receives message
     ↓
Iframe extracts multiplier from game
     ↓
Iframe sends: { type: "MULTIPLIER_UPDATE", multiplier: 1.23 }
     ↓
Dashboard receives message
     ↓
Extract and log
```

### Regex Flow
```
Dashboard Component
     ↓
Access iframe.contentDocument
     ↓
Get all text content
     ↓
Apply regex patterns:
  - /(\d+\.\d{2})x/gi
  - /multiplier[:\s]+(\d+\.\d{2})/gi
  - /crash[:\s]*(\d+\.\d{2})/gi
     ↓
Parse first match
     ↓
Extract and log
```

### API Flow
```
Dashboard Component
     ↓
POST /api/game/state
     ↓
Game backend returns:
  { currentMultiplier: 1.23 }
     ↓
Parse response
     ↓
Extract and log
```

## Confidence Scores Explained

| Confidence | Meaning | Method |
|------------|---------|--------|
| 0.99 | Extremely reliable | API |
| 0.95 | Very reliable | PostMessage |
| 0.85 | Reliable | Regex |
| 0.70 | Moderate | OCR |
| 0.50 | Low | Fallback |

## Filtering Results

Only log multipliers with high confidence:

```typescript
startContinuousExtraction(
  iframeRef,
  async (result) => {
    // Only process if confidence > 80%
    if (result.confidence < 0.8) {
      console.warn("⚠️ Low confidence extraction, skipping");
      return;
    }

    // Process result
    setLiveData(prev => ({ ...prev, multiplier: result.multiplier }));
  }
);
```

## Error Handling

```typescript
const result = await extractMultiplier(iframeRef);

if (result.multiplier === null) {
  console.error(`❌ Extraction failed: ${result.error}`);
  console.log(`Attempted method: ${result.method}`);
} else {
  console.log(`✅ Extracted: ${result.multiplier}x via ${result.method}`);
}
```

## Console Output Example

When using continuous extraction:

```
🎮 Multiplier: 1.05x
📊 Method: regex
✅ Confidence: 85%

🎮 Multiplier: 1.23x
📊 Method: regex
✅ Confidence: 85%

🎮 Multiplier: 1.89x
📊 Method: regex
✅ Confidence: 85%

⚠️ Low confidence extraction, skipping

🎮 Multiplier: 2.15x
📊 Method: api
✅ Confidence: 99%
```

## Iframe Implementation (For Game Provider)

If you control the iframe/game, implement PostMessage support:

```javascript
// Inside game iframe
window.addEventListener("message", (event) => {
  if (event.data.type === "GET_MULTIPLIER") {
    // Get current multiplier from game engine
    const multiplier = gameEngine.getCurrentMultiplier();

    event.source.postMessage({
      type: "MULTIPLIER_UPDATE",
      multiplier: multiplier,
      confidence: 0.99
    }, "*");
  }
});
```

## Performance Considerations

### Extraction Frequency
- **100ms**: Very CPU intensive, not recommended
- **300ms**: Balanced, good for high-precision tracking
- **500ms**: Default, sufficient for most use cases
- **1000ms**: Low CPU usage, might miss fast changes

### Method Overhead
1. **PostMessage**: ~5ms
2. **Regex**: ~10ms
3. **API**: ~50-200ms (network latency)
4. **OCR**: ~500ms (requires Tesseract.js)

### Optimization Tips
```typescript
// Batch processing - log every 10 changes instead of all
let changeCount = 0;

startContinuousExtraction(
  iframeRef,
  async (result) => {
    changeCount++;
    if (changeCount % 10 === 0) {
      // Log every 10 changes
      await logMultiplier({ ... });
    }
  },
  300
);
```

## Troubleshooting

### Q: "Cannot access iframe DOM" error
**A:** The iframe is cross-origin. Solutions:
- Use PostMessage method instead
- Use API method if available
- Configure CORS headers

### Q: No multiplier pattern found
**A:** The regex patterns don't match your iframe format. Solutions:
- Add custom regex patterns to `extractMultiplierViaRegex()`
- Use PostMessage method
- Use OCR method with Tesseract.js

### Q: API returns 401 Unauthorized
**A:** SessionId or credentials invalid. Solutions:
- Update session token in request
- Use Regex method instead
- Check API documentation for authentication

### Q: Extraction is too slow (>1000ms)
**A:** Try faster method or reduce frequency:
```typescript
// Use only fast methods
const result = await extractMultiplier(iframeRef, "regex");

// Or reduce check frequency
startContinuousExtraction(iframeRef, onUpdate, 1000);
```

## Future Enhancements

- [ ] WebGL canvas screenshot + OCR
- [ ] Machine learning pattern recognition
- [ ] Multiplier prediction (based on history)
- [ ] Multi-iframe support (multiple games)
- [ ] Browser extension for cross-origin access
- [ ] Multiplier change history tracking
- [ ] Anomaly detection (suspicious multipliers)
