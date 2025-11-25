# Iframe Multiplier Extraction - Quick Example

## What You Can Do Now

Extract the **exact multiplier value** from the iframe using multiple methods:

### Method 1: Regex (Fastest, Easiest)
```typescript
import { extractMultiplier } from "@/lib/iframe-extractor";

const iframeRef = useRef<HTMLIFrameElement>(null);

// Extract multiplier value
const result = await extractMultiplier(iframeRef, "regex");

console.log(`Multiplier: ${result.multiplier}x`);  // 1.23
console.log(`Method: ${result.method}`);           // regex
console.log(`Confidence: ${result.confidence}`);   // 0.85
```

### Method 2: PostMessage (Most Reliable)
```typescript
// If the iframe is set up to respond to messages:
const result = await extractMultiplier(iframeRef, "postmessage");

console.log(`Multiplier: ${result.multiplier}x`);  // 1.23
console.log(`Confidence: ${result.confidence}`);   // 0.95
```

### Method 3: API (Most Accurate)
```typescript
// If the game has a backend API:
const result = await extractMultiplier(iframeRef, "api");

console.log(`Multiplier: ${result.multiplier}x`);  // 1.23
console.log(`Confidence: ${result.confidence}`);   // 0.99
```

### Method 4: Auto (Try All)
```typescript
// Automatically tries all methods and returns best result:
const result = await extractMultiplier(iframeRef, "auto");

console.log(`Multiplier: ${result.multiplier}x`);
console.log(`Method used: ${result.method}`);      // Whatever worked best
```

## Real-Time Extraction

Track multiplier changes continuously:

```typescript
import { startContinuousExtraction } from "@/lib/iframe-extractor";

useEffect(() => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Extract every 500ms and get updates
  const stop = startContinuousExtraction(
    iframeRef,
    (result) => {
      if (result.multiplier) {
        console.log(`Real-time: ${result.multiplier}x`);
        setCurrentMultiplier(result.multiplier);
      }
    },
    500 // Check every 500ms
  );

  return () => stop(); // Cleanup
}, []);
```

## Integration with Database Logging

```typescript
import {
  startContinuousExtraction
} from "@/lib/iframe-extractor";
import { logMultiplier } from "@/lib/api";

useEffect(() => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Extract and log to database
  const stop = startContinuousExtraction(
    iframeRef,
    async (result) => {
      // Only log high-confidence extractions
      if (result.confidence < 0.8) return;

      // Log to database
      await logMultiplier({
        bot_id: "demo_bot",
        multiplier: result.multiplier,
        round_id: currentRoundId,
        ocr_confidence: result.confidence,
        timestamp: result.timestamp
      });

      console.log(
        `💾 Logged: ${result.multiplier}x ` +
        `(${result.method}, ${(result.confidence*100).toFixed(0)}% confidence)`
      );
    },
    300 // Check every 300ms
  );

  return () => stop();
}, [currentRoundId]);
```

## What Extraction Methods Do

### Regex Method
```
Iframe Content:
  "Current: 1.23x"
  "Multiplier reached 1.23"

Regex Patterns:
  /(\d+\.\d{2})x/
  /multiplier[:\s]+(\d+\.\d{2})/

Result: 1.23
```

### PostMessage Method
```
Dashboard                    Iframe
    ↓                           ↓
  Send:                      Listen:
  { type:                    window.addEventListener(
    "GET_MULTIPLIER"           "message"
  }                          )
    ↓                           ↓
                            Extract from game
                               ↓
  Receive:                   Send:
  { type:                    { type:
    "MULTIPLIER_UPDATE",       "MULTIPLIER_UPDATE",
    multiplier: 1.23           multiplier: 1.23
  }                          }
```

### API Method
```
Dashboard                    Game Backend
    ↓                           ↓
  Request:                   Get game state
  GET /api/game/state
    ↓                           ↓
                            Return:
                            { currentMultiplier: 1.23 }
    ↓
  Parse response
  Extract: 1.23
```

## Console Output Examples

### Successful Extraction
```
✅ Multiplier extracted: 1.23x
📊 Method: regex
✅ Confidence: 85%
💾 Logged to database (record_id: 456)

✅ Multiplier extracted: 1.45x
📊 Method: regex
✅ Confidence: 85%
💾 Logged to database (record_id: 457)

✅ Multiplier extracted: 1.89x
📊 Method: regex
✅ Confidence: 85%
💾 Logged to database (record_id: 458)
```

### With Errors
```
⚠️ Extraction failed: Cannot access iframe DOM
📊 Attempted: regex

✅ Falling back to PostMessage method...

✅ Multiplier extracted: 1.23x
📊 Method: postmessage
✅ Confidence: 95%
```

## Key Features

✅ **Multiple Methods**
- Regex (fast, no special setup)
- PostMessage (reliable, needs iframe support)
- API (accurate, needs backend)
- OCR (highest accuracy, needs library)

✅ **Confidence Scoring**
- Know how reliable each extraction is
- Filter out low-confidence results
- Use confidence for decision-making

✅ **Real-Time Tracking**
- Continuous extraction at intervals
- Only callbacks on changes
- Configurable extraction frequency

✅ **Error Handling**
- Graceful fallbacks
- Clear error messages
- Doesn't crash on failure

✅ **Database Integration**
- Extract multiplier
- Log to database automatically
- Track extraction method
- Store confidence score

## Usage in Your Current Setup

The extraction system works with your **existing simulated multipliers** and can **replace them** with real iframe extraction:

### Current (Simulated)
```typescript
// Demo mode just updates React state
setLiveData(prev => ({
  ...prev,
  multiplier: currentMultiplier  // Simulated value
}));
```

### With Extraction (Real)
```typescript
// Extract real value from iframe
const result = await extractMultiplier(iframeRef);

setLiveData(prev => ({
  ...prev,
  multiplier: result.multiplier,  // Real value from iframe
  extractionMethod: result.method
}));
```

## Next Steps

1. ✅ **Regex Method** - Works immediately, no setup needed
2. **PostMessage Method** - If you control the iframe, add message listener
3. **API Method** - If game backend has API endpoints
4. **OCR Method** - For highest accuracy, install Tesseract.js

## Testing

Try it manually:

```typescript
import { extractMultiplier } from "@/lib/iframe-extractor";

// In browser console or component
const iframeRef = { current: document.querySelector("iframe") };
const result = await extractMultiplier(iframeRef, "regex");
console.log(result);
```

Expected output:
```javascript
{
  multiplier: 1.23,
  method: "regex",
  confidence: 0.85,
  rawValue: "1.23x",
  timestamp: "2025-11-25T12:34:56.789Z"
}
```

---

**Summary**: You now have a complete system to extract the exact multiplier value from the iframe and save it to the database! Use the Regex method for quick testing, then switch to PostMessage or API for production.
