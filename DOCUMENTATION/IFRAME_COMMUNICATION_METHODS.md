# Iframe Communication Methods - Complete Guide

## Overview
Multiple methods exist to communicate with iframes and extract data. You're currently using **postMessage**, but here's a comprehensive breakdown of ALL available methods with their pros/cons.

---

## 1. PostMessage (Currently Used)

### What It Does
Two-way messaging between parent and iframe using structured message passing.

### Code
```typescript
// SENDING (Parent → Iframe)
iframe.contentWindow?.postMessage(
  { type: "GET_MULTIPLIER", data: {...} },
  "https://demo.aviatrix.bet"  // Target origin
);

// RECEIVING (Parent listens to Iframe responses)
window.addEventListener("message", (event) => {
  if (event.origin !== "https://demo.aviatrix.bet") return;
  console.log("Iframe says:", event.data);
});
```

### Message Types to Try
```typescript
const messages = [
  // Basic handshake
  { type: "INIT", client: "dashboard", timestamp: Date.now() },
  { type: "HANDSHAKE" },
  { type: "PING" },

  // State requests
  { type: "GET_STATE" },
  { type: "GET_GAME_STATE" },
  { type: "GET_MULTIPLIER" },
  { type: "GET_STATUS" },

  // Subscriptions
  { type: "SUBSCRIBE", events: ["multiplier", "status", "crash"] },
  { type: "UNSUBSCRIBE", events: ["multiplier"] },

  // Commands
  { type: "PLACE_BET", stake: 25, target: 2.0 },
  { type: "CASH_OUT" },
  { type: "PAUSE" },
  { type: "RESUME" },

  // Extended events
  { type: "ON_ROUND_START" },
  { type: "ON_MULTIPLIER_UPDATE", value: 1.23 },
  { type: "ON_CRASH", value: 2.45 },
];
```

### Pros
✅ Officially supported cross-origin communication
✅ Secure (origin checking built-in)
✅ Two-way messaging
✅ Works with different domains
✅ No CORS issues (uses explicit origin parameter)

### Cons
❌ Requires iframe to listen and respond
❌ May be blocked by iframe's security policy
❌ Asynchronous (delays in response)
❌ Requires knowledge of iframe's API

### Best For
- When iframe supports postMessage API
- Secure cross-origin communication
- Real-time event subscriptions

---

## 2. DOM Access (Direct Element Access)

### What It Does
Directly access and manipulate iframe DOM via `contentDocument` or `contentWindow`.

### Code
```typescript
const iframe = document.querySelector('iframe');
const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;

// READ: Get multiplier value
const multiplierElement = iframeDoc?.querySelector('[data-multiplier]');
const multiplier = multiplierElement?.textContent;

// WRITE: Set game state (if allowed)
const input = iframeDoc?.querySelector('input[name="stake"]');
if (input) {
  input.value = "25";
  input.dispatchEvent(new Event('change', { bubbles: true }));
}

// EXECUTE: Call iframe functions
const gameObject = (iframe.contentWindow as any).Game;
if (gameObject) {
  gameObject.placeBet(25, 2.0);
}
```

### Selector Methods
```typescript
// By ID
iframeDoc?.getElementById('multiplier')

// By CSS class
iframeDoc?.querySelector('.game-multiplier')

// By attribute
iframeDoc?.querySelector('[data-value]')

// By XPath (as you're using)
const xpathResult = iframeDoc?.evaluate(
  '//*[@id="root"]/div[1]/div[3]/div[2]/div[2]',
  iframeDoc,
  null,
  XPathResult.FIRST_ORDERED_NODE_TYPE
);
const element = xpathResult?.singleNodeValue;

// By tag name
iframeDoc?.getElementsByTagName('span')[0]

// Complex selectors
iframeDoc?.querySelectorAll('div.game-container span.multiplier')
```

### Event Triggering
```typescript
// Listen to iframe DOM changes
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'characterData') {
      console.log('Text changed:', mutation.target.textContent);
    }
  });
});

const targetElement = iframeDoc?.querySelector('.multiplier');
observer.observe(targetElement, {
  characterData: true,
  subtree: true
});

// Trigger events
const element = iframeDoc?.querySelector('button.bet');
element?.click();

const input = iframeDoc?.querySelector('input');
input?.focus();
input?.dispatchEvent(new Event('input', { bubbles: true }));
```

### Pros
✅ Real-time DOM access (no delays)
✅ Can trigger clicks and events
✅ Works even if postMessage is blocked
✅ Can read and write all accessible elements
✅ Fast (synchronous)

### Cons
❌ Only works if iframe is same-origin or no X-Frame-Options
❌ Can be blocked by CORS / X-Frame-Options header
❌ Cannot modify iframe security settings
❌ DOM changes may have selectors that change

### Best For
- Local development (localhost)
- Same-origin iframes
- Real-time DOM monitoring
- Event triggering

---

## 3. API Requests (From Parent)

### What It Does
Make direct API calls to the game backend API that the iframe uses.

### Code
```typescript
// Get current game state
const response = await fetch('https://demo.aviatrix.bet/api/game/state', {
  headers: {
    'Authorization': 'Bearer ' + sessionToken,
    'X-Session-ID': sessionId,
  }
});

const gameState = await response.json();
const multiplier = gameState.currentMultiplier;

// Place bet via API
const betResponse = await fetch('https://demo.aviatrix.bet/api/bets/place', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + sessionToken,
  },
  body: JSON.stringify({
    stake: 25,
    targetMultiplier: 2.0,
    sessionId: sessionId
  })
});
```

### Common API Endpoints to Try
```
GET  /api/game/state           - Get current multiplier
GET  /api/game/status          - Get game status
POST /api/bets/place           - Place a bet
POST /api/bets/cashout         - Cash out
GET  /api/user/balance         - Get balance
GET  /api/stats/history        - Get round history
WS   /ws/game/events           - WebSocket for real-time updates
```

### WebSocket Alternative
```typescript
// Real-time updates via WebSocket
const ws = new WebSocket('wss://demo.aviatrix.bet/ws/game/events');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'SUBSCRIBE',
    events: ['multiplier', 'crash', 'status']
  }));
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Multiplier updated:', update.multiplier);
};
```

### Pros
✅ Works regardless of iframe restrictions
✅ Direct backend access
✅ Can bypass iframe security
✅ WebSocket for real-time data
✅ Works cross-origin (CORS permitting)

### Cons
❌ May require authentication tokens
❌ Depends on API documentation
❌ CORS restrictions on backend
❌ May not be publicly documented
❌ Rate limiting on backend

### Best For
- Bypassing iframe security restrictions
- Real-time WebSocket updates
- Complete game state access
- Production systems

---

## 4. Service Worker Interception

### What It Does
Intercept network requests between iframe and server using Service Worker.

### Code
```typescript
// Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(reg => {
    console.log('SW registered');
  });
}

// In service worker (sw.js):
self.addEventListener('fetch', event => {
  if (event.request.url.includes('game/state')) {
    // Intercept game state requests
    event.respondWith(
      fetch(event.request).then(response => {
        const cloned = response.clone();
        cloned.json().then(data => {
          console.log('Game state:', data);
          // Send to parent window
          self.clients.matchAll().then(clients => {
            clients.forEach(client => {
              client.postMessage({
                type: 'GAME_STATE',
                data: data
              });
            });
          });
        });
        return response;
      })
    );
  }
});

// Listen in parent window
navigator.serviceWorker.addEventListener('message', event => {
  if (event.data.type === 'GAME_STATE') {
    console.log('Intercepted:', event.data.data);
  }
});
```

### Pros
✅ Transparent interception (iframe doesn't know)
✅ Access all network requests
✅ Can modify requests/responses
✅ Works cross-origin

### Cons
❌ Requires HTTPS in production
❌ Complex setup
❌ Affects all network traffic
❌ May have performance impact

### Best For
- Network debugging
- Request modification
- Transparent monitoring

---

## 5. Local Storage / SessionStorage

### What It Does
Use shared storage (if same-origin) to pass data between parent and iframe.

### Code
```typescript
// Parent writes to storage
localStorage.setItem('game-state', JSON.stringify({
  stake: 25,
  target: 2.0,
  command: 'place-bet'
}));

// Iframe reads from storage
const gameState = JSON.parse(localStorage.getItem('game-state') || '{}');

// Listen for storage changes
window.addEventListener('storage', event => {
  if (event.key === 'game-state') {
    console.log('Game state changed:', event.newValue);
  }
});
```

### Pros
✅ Simple persistent storage
✅ Works same-origin
✅ No network overhead
✅ Cross-tab communication

### Cons
❌ Only same-origin
❌ Limited storage (~5-10MB)
❌ Slower than memory
❌ Requires storage permissions

### Best For
- Same-origin iframes
- Persistent configuration
- Simple data passing

---

## 6. SharedWorker / Dedicated Worker

### What It Does
Use Web Workers for background communication and computation.

### Code
```typescript
// Parent creates worker
const worker = new Worker('game-monitor.worker.ts');

// Send data to worker
worker.postMessage({
  type: 'ANALYZE_GAME_STATE',
  data: gameState
});

// Receive results
worker.onmessage = (event) => {
  console.log('Worker result:', event.data);
};

// In worker (game-monitor.worker.ts):
self.onmessage = (event) => {
  const { type, data } = event.data;

  if (type === 'ANALYZE_GAME_STATE') {
    const analysis = analyzeState(data);
    self.postMessage(analysis);
  }
};
```

### Pros
✅ Offload heavy computation
✅ Non-blocking (runs in background)
✅ SharedWorker can serve multiple tabs

### Cons
❌ Limited to same-origin
❌ Adds complexity
❌ Browser support varies

### Best For
- Heavy data processing
- Continuous monitoring
- Cross-tab coordination

---

## 7. Beacon API (One-way)

### What It Does
Send small amounts of data to server (one-way, fire-and-forget).

### Code
```typescript
// Send multiplier update to analytics
navigator.sendBeacon('/api/analytics/multiplier', JSON.stringify({
  multiplier: 2.45,
  timestamp: Date.now(),
  sessionId: sessionId
}));

// Good for logging without blocking
window.addEventListener('beforeunload', () => {
  navigator.sendBeacon('/api/session/end', JSON.stringify({
    sessionId: sessionId,
    endTime: Date.now()
  }));
});
```

### Pros
✅ Lightweight
✅ Works even on page unload
✅ Guaranteed delivery (uses queue)

### Cons
❌ One-way only (no response)
❌ No real-time updates
❌ Limited data size

### Best For
- Logging
- Analytics
- Session tracking

---

## 8. IndexedDB / Cache API

### What It Does
Persistent browser database for complex data.

### Code
```typescript
// Store game history
const request = indexedDB.open('GameDB', 1);

request.onsuccess = (event) => {
  const db = (event.target as IDBOpenDBRequest).result;
  const tx = db.transaction('rounds', 'readwrite');
  const store = tx.objectStore('rounds');

  store.add({
    roundId: 123,
    multiplier: 2.45,
    timestamp: Date.now()
  });
};

// Query stored data
const getAllRounds = async () => {
  const request = indexedDB.open('GameDB', 1);
  const db = await new Promise((resolve) => {
    request.onsuccess = () => resolve(request.result);
  });

  const tx = db.transaction('rounds', 'readonly');
  const store = tx.objectStore('rounds');
  return await new Promise((resolve) => {
    store.getAll().onsuccess = () =>
      resolve(store.getAll().result);
  });
};
```

### Pros
✅ Large storage (GB+)
✅ Persistent across sessions
✅ Queryable database
✅ Async API

### Cons
❌ Complex to use
❌ Only same-origin
❌ Slower than memory

### Best For
- Game history storage
- Persistent caching
- Complex data queries

---

## 9. URL Parameters / Fragment Identifier

### What It Does
Pass data via iframe src URL or fragment.

### Code
```typescript
// Set data in iframe URL
const iframeUrl = new URL('https://demo.aviatrix.bet');
iframeUrl.searchParams.set('sessionId', sessionId);
iframeUrl.searchParams.set('stake', '25');
iframeUrl.searchParams.set('target', '2.0');

iframe.src = iframeUrl.toString();

// Iframe reads from URL
const params = new URLSearchParams(window.location.search);
const sessionId = params.get('sessionId');
const stake = params.get('stake');

// Fragment (hash) - doesn't cause reload
iframe.src = 'https://demo.aviatrix.bet#stake=25&target=2.0';

// Listen for hash changes
window.addEventListener('hashchange', () => {
  const params = new URLSearchParams(window.location.hash.slice(1));
  console.log('New params:', params.get('stake'));
});
```

### Pros
✅ Simple parameter passing
✅ Works with any origin
✅ Fragment doesn't cause reload

### Cons
❌ Limited data size (URL length limit)
❌ Public (visible in address bar)
❌ Not secure for sensitive data

### Best For
- Configuration parameters
- Public state
- Session identifiers

---

## 10. Custom Events (Same-Origin Only)

### What It Does
Dispatch and listen to custom events on iframe document.

### Code
```typescript
// Parent dispatches event to iframe
const iframeDoc = iframe.contentDocument;
const event = new CustomEvent('gameBet', {
  detail: { stake: 25, target: 2.0 }
});
iframeDoc?.dispatchEvent(event);

// Iframe listens
document.addEventListener('gameBet', (event: any) => {
  console.log('Bet placed:', event.detail);
});

// Iframe dispatches back to parent
const multiplierEvent = new CustomEvent('multiplierUpdate', {
  detail: { value: 1.23, timestamp: Date.now() }
});
window.parent.document.dispatchEvent(multiplierEvent);

// Parent listens
window.addEventListener('multiplierUpdate', (event: any) => {
  console.log('Multiplier:', event.detail.value);
});
```

### Pros
✅ Natural event-driven
✅ Clean API
✅ Can pass complex objects

### Cons
❌ Same-origin only
❌ Must have DOM access
❌ Events don't persist

### Best For
- Same-origin iframes
- Event-driven architecture
- Real-time updates

---

## Comparison Table

| Method | Real-Time | Cross-Origin | Secure | Ease | Speed | Use Case |
|--------|-----------|--------------|--------|------|-------|----------|
| **PostMessage** | ✅ | ✅ | ✅✅ | Easy | Medium | Event subscriptions |
| **DOM Access** | ✅ | ❌ | ❌ | Easy | Fast | Local dev, same-origin |
| **API Requests** | ✅ | ✅ | ✅ | Medium | Medium | Backend access |
| **WebSocket** | ✅ | ✅ | ✅✅ | Hard | Fast | Real-time events |
| **Service Worker** | ✅ | ✅ | ✅ | Hard | Fast | Network interception |
| **Storage** | ⚠️ | ❌ | ❌ | Easy | Medium | Config, persistent |
| **Worker** | ✅ | ✅ | ✅ | Medium | Fast | Processing |
| **Beacon** | ❌ | ✅ | ✅ | Easy | Fast | Logging |
| **IndexedDB** | ❌ | ❌ | ❌ | Hard | Medium | Storage |
| **URL Params** | ❌ | ✅ | ❌ | Easy | Fast | Configuration |
| **Custom Events** | ✅ | ❌ | ❌ | Easy | Fast | Same-origin events |

---

## Recommended Approach for Your Game

### Primary (Best)
```typescript
// 1. Try XPath DOM extraction (fast, real-time)
const multiplier = extractViaDOM('//*[@id="root"]/div[1]/div[3]/div[2]/div[2]');

// 2. Fallback to postMessage (secure, cross-origin)
const result = await sendPostMessage({ type: 'GET_MULTIPLIER' });

// 3. Fallback to API (if backend provides it)
const state = await fetch('/api/game/state');

// 4. Fallback to MutationObserver (monitor DOM changes)
observeMultiplierChanges();
```

### Implementation Priority
```typescript
const EXTRACTION_METHODS = [
  'xpath-dom',        // Fastest, real-time
  'postmessage',      // Secure, requires iframe support
  'api-direct',       // Reliable, requires backend
  'mutation-observer', // Guaranteed to catch changes
  'fallback-regex',   // Last resort text search
];
```

---

## Testing Each Method

```typescript
async function testAllMethods(iframeRef) {
  const results = {
    xpath: await extractViaXPath(iframeRef),
    postMessage: await testPostMessage(iframeRef),
    domAccess: await accessDOM(iframeRef),
    api: await callAPI(),
    mutationObserver: await observeDOM(iframeRef),
  };

  console.table(results);

  // Find fastest method
  const fastest = Object.entries(results)
    .sort((a, b) => (a[1].time || Infinity) - (b[1].time || Infinity))[0];

  console.log('Recommended:', fastest[0]);
  return fastest;
}
```

---

## Next Steps

Choose your strategy based on:
1. **Same-origin?** → Use DOM Access (fastest)
2. **Cross-origin?** → Use PostMessage or API
3. **No iframe support?** → Use DOM Scanner or XPath
4. **Need persistence?** → Use IndexedDB or Storage
5. **Real-time?** → Use WebSocket or MutationObserver

**For your Aviator game:** XPath DOM extraction + MutationObserver is your best bet for real-time multiplier tracking!

---

**Last Updated**: 2025-11-25
**Version**: 1.0
