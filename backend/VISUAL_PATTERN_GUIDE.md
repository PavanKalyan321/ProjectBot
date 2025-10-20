# Visual Pattern Guide

## Overview

The bot now displays a **visual bar chart** showing the last 10 rounds and identifies the current pattern/trend.

---

## Example Output

```
  [PEAK] Last hour: 383.80x | 5m: 383.80x | 10m: 383.80x | 20m: 383.80x | 30m: 383.80x

  LAST 10 ROUNDS:
  --------------------------------------------------
   1. [LOW      ] .. 1.06x
   2. [LOW      ] .. 1.45x
   3. [LOW      ] .. 1.40x
   4. [LOW      ] ... 1.79x
   5. [LOW      ] ... 1.77x
   6. [MED      ] oooooooo 4.48x
   7. [HIGH     ] ************************************* 18.88x
   8. [LOW      ] ... 1.89x
   9. [LOW      ] .. 1.02x
  10. [LOW      ] .. 1.02x
  --------------------------------------------------

  LEGEND: . = <2x | o/O = 2-10x | * = 10-20x | # = 20x+

  [PATTERN] COLD STREAK - High multiplier likely soon (Position 2 active)
```

---

## Visual Legend

| Symbol | Range | Meaning |
|--------|-------|---------|
| `.` | < 2.0x | Low multiplier |
| `o` | 2.0 - 5.0x | Medium (lower) |
| `O` | 5.0 - 10.0x | Medium (higher) |
| `*` | 10.0 - 20.0x | High multiplier |
| `#` | 20.0x+ | Very high multiplier |

**Bar Length**: Scaled to multiplier value (longer = higher)

---

## Pattern Recognition Rules

The bot analyzes the last 10 rounds and identifies one of these patterns:

### 1. **COLD STREAK**
```
  [PATTERN] COLD STREAK - High multiplier likely soon (Position 2 active)
```
- **Condition**: 7+ low multipliers (< 2.0x) in last 10 rounds
- **What it means**: Game is in a cold phase, high multiplier expected soon
- **Bot behavior**: Position 2 strategy activates, ready to bet on 3x+ target
- **Visual example**:
  ```
   1. [LOW] .. 1.06x
   2. [LOW] .. 1.45x
   3. [LOW] ... 1.79x
   4. [LOW] .. 1.40x
   5. [LOW] ... 1.77x
   6. [LOW] .. 1.06x
   7. [LOW] .. 1.45x
   8. [LOW] ... 1.89x
   9. [LOW] .. 1.02x
  10. [LOW] .. 1.02x
  ```

### 2. **BURST PATTERN**
```
  [PATTERN] BURST PATTERN - Just had high mult(s), expect cooldown
```
- **Condition**: 2+ very high multipliers (≥ 20.0x) in last 10 rounds
- **What it means**: Just experienced high multipliers, cooldown expected
- **Bot behavior**: Cautious, likely to skip rounds
- **Visual example**:
  ```
   1. [MED] ooooo 2.50x
   2. [VERY HIGH] ########################################## 25.00x
   3. [LOW] .. 1.20x
   4. [LOW] ... 1.80x
   5. [HIGH] ************************ 12.50x
   6. [LOW] .. 1.30x
   7. [VERY HIGH] ################################################################ 32.00x
   8. [LOW] .. 1.10x
   9. [MED] ooooooo 3.50x
  10. [LOW] .. 1.05x
  ```

### 3. **HOT PHASE**
```
  [PATTERN] HOT PHASE - Multiple high multipliers detected
```
- **Condition**: 3+ high multipliers (≥ 10.0x) in last 10 rounds
- **What it means**: Game is producing frequent high multipliers
- **Bot behavior**: Opportunistic betting on medium targets
- **Visual example**:
  ```
   1. [HIGH] ******************** 10.50x
   2. [MED] ooooo 2.50x
   3. [HIGH] ********************** 11.20x
   4. [LOW] ... 1.75x
   5. [MED] oooooo 3.20x
   6. [HIGH] ************************ 12.80x
   7. [MED] oooooooo 4.00x
   8. [LOW] .. 1.30x
   9. [HIGH] ************************** 13.50x
  10. [MED] ooooo 2.60x
  ```

### 4. **MIXED PATTERN**
```
  [PATTERN] MIXED PATTERN - No clear trend
```
- **Condition**: 4+ low AND 4+ medium multipliers
- **What it means**: Mix of low and medium, no clear direction
- **Bot behavior**: Relies on ML model confidence
- **Visual example**:
  ```
   1. [LOW] .. 1.20x
   2. [MED] oooooo 3.00x
   3. [LOW] ... 1.85x
   4. [MED] ooooooo 3.50x
   5. [LOW] .. 1.30x
   6. [MED] oooooooo 4.20x
   7. [LOW] .. 1.15x
   8. [MED] oooooo 3.10x
   9. [LOW] ... 1.90x
  10. [MED] ooooooo 3.80x
  ```

### 5. **STABLE PHASE**
```
  [PATTERN] STABLE PHASE - Consistent medium multipliers
```
- **Condition**: 6+ medium multipliers (2.0 - 10.0x)
- **What it means**: Game is stable, consistent payouts
- **Bot behavior**: Position 1 strategy works well
- **Visual example**:
  ```
   1. [MED] oooooo 3.20x
   2. [MED] oooooooo 4.50x
   3. [MED] oooooo 3.00x
   4. [MED] ooooooooo 4.80x
   5. [MED] ooooo 2.70x
   6. [MED] oooooooo 4.20x
   7. [MED] ooooooo 3.90x
   8. [MED] oooooo 3.30x
   9. [MED] ooooo 2.50x
  10. [MED] oooooooo 4.60x
  ```

### 6. **RANDOM PATTERN**
```
  [PATTERN] RANDOM PATTERN - No clear pattern detected
```
- **Condition**: None of the above patterns match
- **What it means**: Game is unpredictable, no discernible pattern
- **Bot behavior**: Conservative, waits for stronger signals
- **Visual example**:
  ```
   1. [LOW] .. 1.40x
   2. [HIGH] ******************** 10.20x
   3. [MED] ooooo 2.80x
   4. [LOW] ... 1.95x
   5. [HIGH] ************************ 12.50x
   6. [LOW] .. 1.20x
   7. [MED] oooooooo 4.30x
   8. [LOW] .. 1.10x
   9. [MED] oooooo 3.10x
  10. [LOW] ... 1.60x
  ```

---

## How Patterns Affect Betting Strategy

| Pattern | Position 1 (1.5-2.0x) | Position 2 (3.0x+) | Bet Frequency |
|---------|------------------------|---------------------|---------------|
| **COLD STREAK** | Low confidence | **HIGH confidence** | Moderate (waits for 7+ cold) |
| **BURST PATTERN** | Medium confidence | Low confidence | Low (cooling down) |
| **HOT PHASE** | **HIGH confidence** | Medium confidence | High |
| **MIXED PATTERN** | Medium confidence | Low confidence | Moderate |
| **STABLE PHASE** | **HIGH confidence** | Low confidence | High |
| **RANDOM PATTERN** | Low confidence | Low confidence | Low (waits for pattern) |

---

## Reading the Display

### Peak Values
```
[PEAK] Last hour: 383.80x | 5m: 383.80x | 10m: 383.80x | 20m: 383.80x | 30m: 383.80x
```
Shows the highest multiplier seen in each time window.

### Visual Chart
```
  LAST 10 ROUNDS:
  --------------------------------------------------
   1. [LOW      ] .. 1.06x          <- Round #1 (oldest)
   2. [LOW      ] .. 1.45x
   ...
  10. [LOW      ] .. 1.02x          <- Round #10 (most recent)
  --------------------------------------------------
```
- **Top to bottom** = Oldest to newest
- **Bar length** = Multiplier magnitude
- **Symbol** = Category (low/med/high/very high)

### Pattern Summary
```
[PATTERN] COLD STREAK - High multiplier likely soon (Position 2 active)
```
Clear explanation of what's happening and what to expect.

---

## Quick Reference

| What You See | What It Means | What Bot Does |
|--------------|---------------|---------------|
| Many dots (.) | Cold streak | Prepare for Position 2 bet |
| Many o's/O's | Stable phase | Position 1 bets likely |
| Many stars (*) | Hot phase | Active betting window |
| Many hashes (#) | Burst happened | Expect cooldown, skip |
| Mixed symbols | Random/unclear | Wait for clear pattern |

---

## Tips for Users

1. **Watch the pattern evolution** - Patterns change every round
2. **Cold streaks are opportunities** - Position 2 targets high multipliers
3. **After bursts, be patient** - Game typically cools down
4. **Stable phases are best for Position 1** - Consistent 1.5-2.0x targets
5. **Trust the visual** - It's based on actual last 10 rounds

---

## Summary

The visual representation gives you instant insight into:
- ✅ Recent round history (last 10)
- ✅ Magnitude of each multiplier
- ✅ Current pattern/trend
- ✅ What strategy the bot is likely to use
- ✅ Peak multipliers across time windows

All in a **clean, easy-to-read format** that updates after every round!
