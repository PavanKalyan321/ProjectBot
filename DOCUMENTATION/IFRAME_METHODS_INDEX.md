# Iframe Communication Methods - Complete Index

## 📚 Documentation Overview

You now have comprehensive documentation on **10 iframe communication methods**. Here's your roadmap:

---

## 🎯 Start Here Based on Your Need

### "I want to extract multiplier values from the iframe"
```
1. Read: COMMUNICATION_METHODS_SUMMARY.md (2 min overview)
2. Read: IFRAME_COMMUNICATION_METHODS.md (detailed guide)
3. Try: testAllMethods() to see what works (5 min test)
4. Use: extractMultiplierMultiMethod() (automatic selection)
```

### "I want to understand all available methods"
```
1. Read: COMMUNICATION_METHODS_SUMMARY.md (overview)
2. Read: IFRAME_COMMUNICATION_METHODS.md (all 10 methods detailed)
3. Skim: TEST_IFRAME_METHODS.md (testing each one)
4. Code: src/lib/iframe-communication.ts (implementation)
```

### "I want to test if specific methods work with my iframe"
```
1. Read: TEST_IFRAME_METHODS.md (testing guide)
2. Run: testAllMethods(iframeRef) in browser console
3. Review: Results to see what works
4. Implement: Best working method(s)
```

### "I want to set up real-time multiplier monitoring"
```
1. Use: setupMutationObserver() - Method 2 (best for real-time)
2. Or: sendPostMessage() - Method 1 (secure, cross-origin)
3. Or: callIframeFunction() - Method 5 (if API available)
```

### "I want quick copy-paste code examples"
```
1. Look for code blocks in: COMMUNICATION_METHODS_SUMMARY.md
2. Or: TEST_IFRAME_METHODS.md (has examples for each)
3. Or: src/lib/iframe-communication.ts (fully documented functions)
```

---

## 📖 Document Guide

### COMMUNICATION_METHODS_SUMMARY.md
**Best for**: Quick overview, decision tree, when to use what
**Read time**: 5-10 minutes
**Contains**:
- Overview of all 10 methods
- Quick decision tree
- When to use each method
- Performance comparison
- Integration example
- Troubleshooting

### IFRAME_COMMUNICATION_METHODS.md
**Best for**: Deep understanding, detailed explanations, pros/cons
**Read time**: 20-30 minutes
**Contains**:
- All 10 methods detailed
- Code examples for each
- Pros and cons for each
- Best use cases
- Comparison table
- Advanced usage

### TEST_IFRAME_METHODS.md
**Best for**: Testing each method, debugging, validation
**Read time**: 15-20 minutes (but most reading is code examples)
**Contains**:
- How to test each method
- Messages to try for PostMessage
- Objects to explore for Window access
- Functions to call
- Expected results
- Debugging tips
- Complete testing suite example

### src/lib/iframe-communication.ts
**Best for**: Implementation reference, copy-paste code
**Contains**:
- `sendPostMessage()` - Method 1: PostMessage API
- `setupMutationObserver()` - Method 2: DOM Changes
- `simulateClick()` - Method 3: Click Events
- `accessWindowObject()` - Method 4: Window Objects
- `callIframeFunction()` - Method 5: Function Calls
- `searchIframeText()` - Method 6: Regex Search
- `interceptConsole()` - Method 7: Console Logs
- `watchStorage()` - Method 8: Storage Changes
- `observePerformance()` - Method 9: Network Monitoring
- `extractMultiplierMultiMethod()` - Method 10: Auto-Fallback
- `testAllMethods()` - Testing helper

---

## 🔍 Quick Reference by Use Case

### Extract Multiplier Value (One-Time)
```typescript
// Best: Multi-Method Fallback
import { extractMultiplierMultiMethod } from '@/lib/iframe-communication';
const result = await extractMultiplierMultiMethod(iframeRef);
console.log('Multiplier:', result.value, 'Method:', result.method);
```

### Monitor Multiplier Changes (Real-Time)
```typescript
// Best: Mutation Observer
import { setupMutationObserver } from '@/lib/iframe-communication';
const unsubscribe = setupMutationObserver(
  iframeRef,
  '.multiplier-display',
  (oldVal, newVal) => console.log(`${oldVal} → ${newVal}`)
);
```

### Send Command to Iframe
```typescript
// Best: PostMessage
import { sendPostMessage } from '@/lib/iframe-communication';
const result = await sendPostMessage(iframeRef, {
  type: "PLACE_BET",
  stake: 25,
  target: 2.0
});
```

### Trigger Game Action
```typescript
// Best: Click Simulation
import { simulateClick } from '@/lib/iframe-communication';
simulateClick(iframeRef, 'button.place-bet-button');
```

### Access Game State Directly
```typescript
// Best: Window Object Access
import { accessWindowObject } from '@/lib/iframe-communication';
const gameState = await accessWindowObject(iframeRef, 'Game.state');
console.log('Current state:', gameState.data);
```

### Call Game Function
```typescript
// Best: Call Iframe Function
import { callIframeFunction } from '@/lib/iframe-communication';
const multiplier = await callIframeFunction(iframeRef, 'Game.getMultiplier');
```

### Search for Values by Pattern
```typescript
// Best: Regex Search
import { searchIframeText } from '@/lib/iframe-communication';
const multipliers = searchIframeText(iframeRef, /(\d+\.\d+)x/);
```

### Monitor Network Requests
```typescript
// Best: Performance Observer
import { observePerformance } from '@/lib/iframe-communication';
const perf = observePerformance(iframeRef);
console.log('API calls:', perf.data.requests);
```

### Test What Works
```typescript
// Best: Test All Methods
import { testAllMethods } from '@/lib/iframe-communication';
const results = await testAllMethods(iframeRef);
console.table(results); // Shows which methods work
```

---

## 📊 The 10 Methods

| # | Name | Priority | Latency | Ease | Use Case |
|---|------|----------|---------|------|----------|
| 1️⃣ | PostMessage | 1st | Medium | Easy | Secure cross-origin messaging |
| 2️⃣ | Mutation Observer | 1st | Fast | Easy | Real-time DOM monitoring |
| 3️⃣ | Click Simulation | 2nd | Fast | Easy | Trigger game actions |
| 4️⃣ | Window Object | 2nd | Instant | Medium | Direct API access |
| 5️⃣ | Function Call | 2nd | Medium | Medium | Execute iframe functions |
| 6️⃣ | Regex Search | 3rd | Slow | Easy | Last-resort pattern matching |
| 7️⃣ | Console Intercept | 3rd | Medium | Medium | Debug logging |
| 8️⃣ | Storage Watcher | 3rd | Medium | Easy | Persistent state tracking |
| 9️⃣ | Performance Monitor | 4th | Slow | Hard | Network analysis |
| 🔟 | Multi-Method | 1st | Medium | Easy | Automatic fallback (best reliability) |

---

## 🎓 Learning Path

### Beginner (Just get it working)
```
1. COMMUNICATION_METHODS_SUMMARY.md → Read "Quick Decision Tree"
2. TEST_IFRAME_METHODS.md → Run testAllMethods()
3. TEST_IFRAME_METHODS.md → Find what works
4. src/lib/iframe-communication.ts → Copy working method
5. Integrate into your component
```

### Intermediate (Understand the options)
```
1. COMMUNICATION_METHODS_SUMMARY.md → Read entire document
2. IFRAME_COMMUNICATION_METHODS.md → Read Methods 1-3
3. TEST_IFRAME_METHODS.md → Test Methods 1-3
4. Choose best method for your use case
5. Implement with proper error handling
```

### Advanced (Master all methods)
```
1. IFRAME_COMMUNICATION_METHODS.md → Read all methods
2. TEST_IFRAME_METHODS.md → Test all methods
3. src/lib/iframe-communication.ts → Review implementation
4. Create custom extraction strategy
5. Implement multi-method fallback with your preferences
```

---

## 🚀 Implementation Checklist

### Basic Setup
- [ ] Read COMMUNICATION_METHODS_SUMMARY.md
- [ ] Understand your use case
- [ ] Choose 1-2 primary methods

### Testing
- [ ] Run testAllMethods(iframeRef)
- [ ] Verify what works with your iframe
- [ ] Record results

### Implementation
- [ ] Import method(s) from src/lib/iframe-communication.ts
- [ ] Add to your component
- [ ] Test with real game
- [ ] Add error handling

### Optimization
- [ ] Performance test each method
- [ ] Choose fastest working method
- [ ] Add fallbacks for reliability
- [ ] Monitor in production

### Documentation
- [ ] Document which methods work
- [ ] Record any custom configurations
- [ ] Note any iframe-specific requirements

---

## ⚠️ Important Notes

### Same-Origin vs Cross-Origin
- **Same-origin**: Can use all 10 methods
- **Cross-origin**: Limited to PostMessage (Method 1) and Performance (Method 9)

### Method Availability
- Not all methods work with all iframes
- Always test before relying on a method
- Use `testAllMethods()` to discover what works

### Performance Impact
- Fastest: Window Object Access, Click Simulation
- Medium: PostMessage, Mutation Observer
- Slowest: Regex Search, Console Interception

### Reliability Order
1. Mutation Observer (if real-time)
2. PostMessage (if iframe supports)
3. Window Object (if exposed)
4. Multi-Method Fallback (most reliable, tries all)

---

## 🔧 Integration Template

```typescript
import {
  extractMultiplierMultiMethod,
  setupMutationObserver,
  sendPostMessage,
  accessWindowObject,
} from '@/lib/iframe-communication';

export default function YourComponent({ iframeRef }) {
  const [multiplier, setMultiplier] = useState(1.0);
  const [communicationMethod, setCommunicationMethod] = useState('');

  // Option 1: Real-time monitoring (best for constant updates)
  useEffect(() => {
    const unsubscribe = setupMutationObserver(
      iframeRef,
      '.multiplier', // Adjust selector for your iframe
      (oldVal, newVal) => {
        const num = parseFloat(newVal);
        if (!isNaN(num)) setMultiplier(num);
      }
    );
    return unsubscribe;
  }, []);

  // Option 2: Periodic polling (if real-time not available)
  useEffect(() => {
    const interval = setInterval(async () => {
      const result = await extractMultiplierMultiMethod(iframeRef);
      if (result.value) {
        setMultiplier(result.value);
        if (!communicationMethod) setCommunicationMethod(result.method);
      }
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <p>Multiplier: {multiplier.toFixed(2)}x</p>
      <p>Method: {communicationMethod}</p>
    </div>
  );
}
```

---

## 📞 Support & Debugging

### If Something Doesn't Work
```
1. Check COMMUNICATION_METHODS_SUMMARY.md → Troubleshooting
2. Run TEST_IFRAME_METHODS.md → Run the complete test suite
3. Check browser console for errors
4. Try another method from the list
5. Use extractMultiplierMultiMethod() as fallback
```

### Check iframe Type
```typescript
// In browser console
const iframe = document.querySelector('iframe');
console.log('Origin:', iframe.src);
console.log('Same-origin?', document.domain === new URL(iframe.src).hostname);
```

### List What's Available
```typescript
// In browser console
const iw = document.querySelector('iframe').contentWindow;
console.log(Object.getOwnPropertyNames(iw).filter(p => !p.startsWith('_')));
```

---

## 🎯 Next Steps

1. **Choose your use case** from "Quick Reference by Use Case"
2. **Read the relevant guide** from "Document Guide"
3. **Test the method** using examples from "TEST_IFRAME_METHODS.md"
4. **Implement in your code** using examples from src/lib
5. **Monitor and optimize** based on performance

---

## 📋 File Locations

| File | Purpose | Best For |
|------|---------|----------|
| COMMUNICATION_METHODS_SUMMARY.md | Overview & decision making | Quick answers |
| IFRAME_COMMUNICATION_METHODS.md | Detailed guide | Deep understanding |
| TEST_IFRAME_METHODS.md | Testing & validation | Debugging & testing |
| src/lib/iframe-communication.ts | Implementation | Copy-paste code |
| IFRAME_METHODS_INDEX.md | This file | Navigation |

---

**Version**: 1.0
**Last Updated**: 2025-11-25
**Status**: Complete & Production Ready

---

## Quick Links

- 🚀 [Quick Start](COMMUNICATION_METHODS_SUMMARY.md#quick-decision-tree)
- 📖 [Full Guide](IFRAME_COMMUNICATION_METHODS.md)
- 🧪 [Testing Guide](TEST_IFRAME_METHODS.md)
- 💻 [Implementation](dashboard-nextjs/src/lib/iframe-communication.ts)
- 🔍 [Troubleshooting](COMMUNICATION_METHODS_SUMMARY.md#troubleshooting)
