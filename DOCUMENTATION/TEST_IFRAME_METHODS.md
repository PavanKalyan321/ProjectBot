# Testing Iframe Communication Methods

## Quick Reference

You have **10 different methods** to communicate with iframes. Here's how to test each one:

---

## Setup

First, add this to your component to test all methods:

```typescript
import {
  testAllMethods,
  extractMultiplierMultiMethod,
  setupMutationObserver,
  sendPostMessage,
  accessWindowObject,
} from '@/lib/iframe-communication';

// In your component
const handleTestMethods = async () => {
  console.log('Testing all communication methods...');
  const results = await testAllMethods(iframeRef);
  console.table(results);

  // Also test extraction
  const extraction = await extractMultiplierMultiMethod(iframeRef);
  console.log('Best extraction method:', extraction);
};
```

---

## Method 1: PostMessage

### Test Code
```typescript
// Send message to iframe
const result = await sendPostMessage(iframeRef, {
  type: "GET_MULTIPLIER",
  requestId: "test-001"
});

console.log(result);
// Success: { method: 'postMessage', success: true, data: {...} }
// Failure: { method: 'postMessage', success: false, error: "Timeout..." }
```

### Messages to Try
```typescript
// If these work, iframe has an API:
const testMessages = [
  { type: "PING" },
  { type: "HANDSHAKE" },
  { type: "GET_STATE" },
  { type: "GET_MULTIPLIER" },
  { type: "GET_STATUS" },
  { type: "GET_GAME_STATE" },
  { type: "SUBSCRIBE", events: ["multiplier"] },
];

for (const msg of testMessages) {
  const result = await sendPostMessage(iframeRef, msg, "https://demo.aviatrix.bet", 2000);
  if (result.success) {
    console.log(`✅ ${msg.type} works!`, result.data);
  }
}
```

### Expected Success
```
Multiplier API responds with: { multiplier: 2.45 }
```

---

## Method 2: DOM Mutation Observer

### Test Code
```typescript
import { setupMutationObserver } from '@/lib/iframe-communication';

// Watch for multiplier changes
const unsubscribe = setupMutationObserver(
  iframeRef,
  '.game-multiplier',  // CSS selector
  (oldValue, newValue) => {
    console.log(`Multiplier changed: ${oldValue} → ${newValue}`);
  }
);

// Clean up when done
// unsubscribe();
```

### Expected Success
```
Multiplier changed: 1.00 → 1.23
Multiplier changed: 1.23 → 2.45
Multiplier changed: 2.45 → CRASHED
```

---

## Method 3: Click Simulation

### Test Code
```typescript
import { simulateClick } from '@/lib/iframe-communication';

// Simulate clicking "Place Bet" button
const result = simulateClick(iframeRef, 'button.place-bet');

if (result.success) {
  console.log('✅ Click simulated successfully');
}
```

### Selectors to Try
```typescript
const selectorsToTest = [
  'button.place-bet',
  'button[data-action="bet"]',
  '.game-controls button:first-child',
  'button:contains("Bet")',
  '[data-testid="place-bet-button"]',
];

selectorsToTest.forEach(selector => {
  const result = simulateClick(iframeRef, selector);
  console.log(`${selector}: ${result.success ? '✅' : '❌'}`);
});
```

---

## Method 4: Window Object Access

### Test Code
```typescript
import { accessWindowObject } from '@/lib/iframe-communication';

// Access iframe's game object
const result = await accessWindowObject(iframeRef, 'Game.state.multiplier');

if (result.success) {
  console.log('Current multiplier:', result.data);
}
```

### Objects to Explore
```typescript
const objectsToTest = [
  'window.gameState',
  'window.Game',
  'window.game',
  'window.__APP_STATE__',
  'Game.state',
  'Game.state.multiplier',
  'Game.currentRound',
  'GameManager.instance',
  'window.event',
];

for (const path of objectsToTest) {
  const result = await accessWindowObject(iframeRef, path);
  if (result.success) {
    console.log(`✅ ${path}:`, result.data);
  }
}
```

### Expected Success
```
✅ Game.state.multiplier: 2.45
✅ window.gameState: { multiplier: 2.45, status: "RUNNING" }
```

---

## Method 5: Call Iframe Function

### Test Code
```typescript
import { callIframeFunction } from '@/lib/iframe-communication';

// Call iframe's getMultiplier function
const result = await callIframeFunction(iframeRef, 'Game.getMultiplier');

if (result.success) {
  console.log('Multiplier:', result.data);
}
```

### Functions to Try
```typescript
const functionsToTest = [
  { path: 'Game.getMultiplier', args: [] },
  { path: 'Game.getGameState', args: [] },
  { path: 'Game.placeBet', args: [25, 2.0] },
  { path: 'Game.cashOut', args: [] },
  { path: 'GameManager.instance.getMultiplier', args: [] },
  { path: 'window.getGameState', args: [] },
];

for (const { path, args } of functionsToTest) {
  const result = await callIframeFunction(iframeRef, path, args);
  if (result.success) {
    console.log(`✅ ${path}():`, result.data);
  }
}
```

---

## Method 6: Regex Text Search

### Test Code
```typescript
import { searchIframeText } from '@/lib/iframe-communication';

// Search for multiplier values
const result = searchIframeText(iframeRef, /(\d+\.\d+)\s*[x×]/);

if (result.success) {
  console.log('Found multipliers:', result.data);
  // Output: ['2.45x', '2.50×', ...]
}
```

### Patterns to Test
```typescript
const patternsToTest = [
  /(\d+\.\d{2})/,                    // Decimals like 1.23
  /(\d+\.\d{2})\s*[x×]/,             // With x/×
  /multiplier[:\s]*(\d+\.\d{2})/i,   // Labeled
  /crash[:\s]*(\d+\.\d{2})/i,        // Crash values
  /\b\d+\.\d{2}\b/,                  // Just numbers
];

patternsToTest.forEach(pattern => {
  const result = searchIframeText(iframeRef, pattern);
  if (result.success) {
    console.log(`✅ Pattern ${pattern}:`, result.data);
  }
});
```

---

## Method 7: Console Interception

### Test Code
```typescript
import { interceptConsole } from '@/lib/iframe-communication';

// Intercept iframe console logs containing "multiplier"
const unsubscribe = interceptConsole(iframeRef, (msg) =>
  msg.toLowerCase().includes('multiplier')
);

// Wait and check logs
setTimeout(() => {
  console.log('Intercepted logs from iframe');
  unsubscribe(); // Stop intercepting
}, 5000);
```

---

## Method 8: Storage Watcher

### Test Code
```typescript
import { watchStorage } from '@/lib/iframe-communication';

// Watch localStorage/sessionStorage changes
const unsubscribe = watchStorage(iframeRef, (key, value) => {
  console.log(`Storage changed: ${key} = ${value}`);
});

// Later:
unsubscribe(); // Stop watching
```

---

## Method 9: Performance Monitoring

### Test Code
```typescript
import { observePerformance } from '@/lib/iframe-communication';

// Check what API calls iframe is making
const result = observePerformance(iframeRef);

if (result.success) {
  console.log('API requests:', result.data.requests);
  // Output: [
  //   { url: 'https://api.example.com/game/state', duration: 45, size: 1024 },
  //   ...
  // ]
}
```

---

## Method 10: Multi-Method Fallback

### Test Code
```typescript
import { extractMultiplierMultiMethod } from '@/lib/iframe-communication';

// Try all methods automatically
const result = await extractMultiplierMultiMethod(iframeRef);

console.log('Best working method:', result.method);
console.log('Multiplier value:', result.value);
console.log('All attempts:', result.results);
```

### Output Example
```
{
  value: 2.45,
  method: "postMessage",
  results: [
    { method: "postMessage", success: true, data: {...} },
    { method: "windowObject", success: false, error: "..." },
    { method: "callFunction", success: false, error: "..." },
  ]
}
```

---

## Complete Testing Suite

### Add Test Component
```typescript
'use client';

import { testAllMethods, extractMultiplierMultiMethod } from '@/lib/iframe-communication';

export default function IframeTestSuite({ iframeRef }) {
  const [testResults, setTestResults] = React.useState(null);

  const handleTest = async () => {
    const results = await testAllMethods(iframeRef);
    setTestResults(results);
  };

  return (
    <div className="space-y-4">
      <button onClick={handleTest}>Test All Methods</button>

      {testResults && (
        <div className="bg-slate-800 p-4 rounded">
          <h3>Test Results</h3>
          <pre>{JSON.stringify(testResults, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
```

---

## Expected Results Matrix

| Method | Same-Origin | Cross-Origin | Works | Reason |
|--------|-------------|--------------|-------|--------|
| PostMessage | ✅ | ✅ | If iframe supports API | iframe must listen |
| Mutation Observer | ✅ | ❌ | Maybe | Need DOM access |
| Click Simulation | ✅ | ❌ | Maybe | Need DOM access |
| Window Object | ✅ | ❌ | Maybe | Depends on exposed APIs |
| Call Function | ✅ | ❌ | Maybe | Depends on exposed APIs |
| Regex Search | ✅ | ❌ | Maybe | Need DOM access |
| Console Interception | ✅ | ❌ | Maybe | Need window access |
| Storage Watcher | ✅ | ❌ | Maybe | Need storage access |
| Performance | ✅ | ✅ | ✅ | Always works |
| DOM Scanner | ✅ | ❌ | Maybe | Need DOM access |

---

## Debugging Tips

### If PostMessage Fails
```typescript
// Check if iframe sends any messages
window.addEventListener('message', event => {
  console.log('Message from:', event.origin);
  console.log('Data:', event.data);
});
```

### If DOM Access Fails
```typescript
// Check iframe cross-origin status
const iframe = iframeRef.current;
try {
  const doc = iframe.contentDocument;
  if (!doc) {
    console.error('Cannot access iframe DOM - likely cross-origin');
  }
} catch (e) {
  console.error('Cross-origin error:', e);
}
```

### If Window Object Not Found
```typescript
// List all properties on iframe window
const props = Object.getOwnPropertyNames(iframe.contentWindow);
console.log('Available properties:', props);
```

---

## Recommended Testing Order

```
1. ✅ PostMessage (most compatible)
   ↓ Fails?
2. ✅ DOM Access (if same-origin)
   ↓ Fails?
3. ✅ Window Objects (if exposed)
   ↓ Fails?
4. ✅ Regex Search (last resort)
   ↓ Fails?
5. ✅ DOM Scanner (comprehensive discovery)
```

---

## Integration in LeftIframe

Add test button to your component:

```typescript
{process.env.NODE_ENV === 'development' && (
  <button
    onClick={async () => {
      const result = await extractMultiplierMultiMethod(iframeRef);
      console.log('Method test result:', result);
      addLog('interaction', 'info', `Method test: ${result.method}`, result);
    }}
    className="text-xs px-2 py-1 bg-blue-600 text-white rounded"
  >
    Test Methods
  </button>
)}
```

---

## Next Steps

1. **Run tests** with `testAllMethods()`
2. **Identify working methods** from results
3. **Update extraction** code to use best methods
4. **Add fallbacks** for reliability
5. **Monitor performance** to pick fastest

---

**Version**: 1.0
**Last Updated**: 2025-11-25
