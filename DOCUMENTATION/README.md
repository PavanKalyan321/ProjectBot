# Documentation Index

All documentation for the Aviator Dashboard project is organized here.

## Quick Navigation

### 🚀 Getting Started
- **[START_HERE.md](../START_HERE.md)** - Begin here! Overview and quick start

### 📡 Communication & Extraction
- **[README_AUTORUN.md](README_AUTORUN.md)** - Auto-run communication methods on load
- **[IFRAME_COMMUNICATION_METHODS.md](IFRAME_COMMUNICATION_METHODS.md)** - All 10 communication methods detailed
- **[COMMUNICATION_METHODS_SUMMARY.md](COMMUNICATION_METHODS_SUMMARY.md)** - Overview and decision trees
- **[TEST_IFRAME_METHODS.md](TEST_IFRAME_METHODS.md)** - How to test each method
- **[POSTMESSAGE_EXTRACTION_SETUP.md](POSTMESSAGE_EXTRACTION_SETUP.md)** - Real-time PostMessage extraction
- **[IFRAME_METHODS_INDEX.md](IFRAME_METHODS_INDEX.md)** - Navigation guide for methods

### 🔬 DOM Scanner
- **[DOM_SCANNER_GUIDE.md](DOM_SCANNER_GUIDE.md)** - Complete DOM scanner guide
- **[SCANNER_IMPLEMENTATION_SUMMARY.md](SCANNER_IMPLEMENTATION_SUMMARY.md)** - Scanner implementation details
- **[QUICK_SCAN_START.md](QUICK_SCAN_START.md)** - Quick start for DOM scanning

### 🤖 Auto-Run System
- **[AUTORUN_COMMUNICATION_METHODS.md](AUTORUN_COMMUNICATION_METHODS.md)** - Full auto-run setup details
- **[AUTORUN_QUICK_START.txt](AUTORUN_QUICK_START.txt)** - Visual quick start
- **[AUTORUN_COMPLETE.txt](AUTORUN_COMPLETE.txt)** - Completion status

### 📊 Visual Guides
- **[IFRAME_METHODS_VISUAL.txt](IFRAME_METHODS_VISUAL.txt)** - Visual overview of all methods
- **[FINAL_SUMMARY.txt](FINAL_SUMMARY.txt)** - Final project summary

---

## Directory Structure

```
PROJECT_ROOT/
├── DOCUMENTATION/              ← You are here
│   ├── README.md
│   ├── DOM_SCANNER_GUIDE.md
│   ├── IFRAME_COMMUNICATION_METHODS.md
│   ├── POSTMESSAGE_EXTRACTION_SETUP.md
│   └── ... (all documentation files)
│
├── dashboard-nextjs/           ← Frontend (Next.js)
│   ├── src/
│   │   ├── components/
│   │   │   ├── LeftIframe.tsx         ← Main iframe component
│   │   │   └── IframeDOMScanner.tsx   ← DOM scanner UI
│   │   ├── lib/
│   │   │   ├── iframe-extractor.ts    ← XPath extraction
│   │   │   ├── iframe-communication.ts ← All 10 communication methods
│   │   │   └── iframe-dom-scanner.ts  ← DOM scanning utility
│   │   └── pages/
│   │       └── Dashboard.tsx
│   └── package.json
│
├── backend/                    ← Backend (Python/Flask)
│   ├── dashboard/
│   │   ├── multiplier_api.py   ← Multiplier API routes
│   │   └── compact_analytics.py
│   ├── database/
│   │   └── multiplier_logger.py ← Database logging
│   └── ...
│
├── README.md                   ← Main readme
├── START_HERE.md              ← Entry point
└── ... (other project files)
```

---

## Key Features

### 1. 10 Communication Methods
**File**: `IFRAME_COMMUNICATION_METHODS.md`

Choose from:
1. PostMessage (best for your iframe)
2. Mutation Observer
3. Click Simulation
4. Window Object Access
5. Call Function
6. Regex Search
7. Console Interception
8. Storage Watcher
9. Performance Observer
10. Multi-Method Fallback

### 2. Auto-Run Testing
**File**: `README_AUTORUN.md`

All methods automatically test on iframe load:
- Shows which methods work
- Identifies best method
- Extracts multiplier automatically
- Logs results to Event Log

### 3. DOM Scanner
**File**: `DOM_SCANNER_GUIDE.md`

10-second continuous DOM capture:
- Identifies all multiplier elements
- Generates XPath selectors
- Provides CSS selectors
- Exports JSON/reports

### 4. Real-Time Extraction
**File**: `POSTMESSAGE_EXTRACTION_SETUP.md`

Continuous multiplier polling:
- Polls every 1 second
- Updates display in real-time
- Falls back to XPath if needed
- Logs all changes

---

## Quick Start

1. **Read**: [START_HERE.md](../START_HERE.md)
2. **Understand**: [README_AUTORUN.md](README_AUTORUN.md)
3. **Learn Methods**: [IFRAME_COMMUNICATION_METHODS.md](IFRAME_COMMUNICATION_METHODS.md)
4. **Implement**: Copy code from `src/lib/iframe-communication.ts`

---

## Documentation by Use Case

### I want to extract the multiplier
→ **[POSTMESSAGE_EXTRACTION_SETUP.md](POSTMESSAGE_EXTRACTION_SETUP.md)**

### I want to understand all communication methods
→ **[IFRAME_COMMUNICATION_METHODS.md](IFRAME_COMMUNICATION_METHODS.md)**

### I want to test which methods work
→ **[TEST_IFRAME_METHODS.md](TEST_IFRAME_METHODS.md)**

### I want to scan the DOM for elements
→ **[DOM_SCANNER_GUIDE.md](DOM_SCANNER_GUIDE.md)**

### I want auto-tests on load
→ **[README_AUTORUN.md](README_AUTORUN.md)**

### I want a quick visual overview
→ **[IFRAME_METHODS_VISUAL.txt](IFRAME_METHODS_VISUAL.txt)**

---

## Implementation Files

All code is in the Frontend:

**`dashboard-nextjs/src/lib/`**:
- `iframe-communication.ts` - All 10 methods
- `iframe-extractor.ts` - XPath extraction
- `iframe-dom-scanner.ts` - DOM scanner

**`dashboard-nextjs/src/components/`**:
- `LeftIframe.tsx` - Main component with auto-tests
- `IframeDOMScanner.tsx` - DOM scanner UI

---

## Status

✅ **All 10 communication methods** - Implemented
✅ **Auto-run testing** - Active on load
✅ **PostMessage extraction** - Real-time polling
✅ **DOM scanner** - 10-second capture
✅ **Event logging** - Full visibility

---

## Version Info

**Version**: 1.0
**Last Updated**: 2025-11-25
**Status**: Production Ready

---

**See [START_HERE.md](../START_HERE.md) to begin!**
