# Configuration Usage - How Bot Uses Your Settings

## Overview

The bot **actively uses all user-provided configuration** throughout its operation. Every parameter you set at startup is used in real-time decision-making and betting operations.

---

## Configuration Flow

```
User Input at Startup
     ↓
Stored in bot.config_manager
     ↓
Used Throughout Runtime
     ↓
Applied to Every Decision
```

---

## Configuration Parameters & Usage

### 1. **Initial Stake**

**How You Set It:**
```
Initial stake (default 25): 50
```

**Where It's Used:**
- **Line 86**: Initialize bot's starting stake
- **Line 591**: Used as `stake_used` when placing bets
- **Line 559, 671, 730, 770, 863**: Reset stake after losses

**Real-Time Example:**
```
🎯 ROUND #001
  ✅ DECISION: PLACE BET
  💰 Stake: 50  ← Your input used here!
```

---

### 2. **Max Stake**

**How You Set It:**
```
Max stake (default 500): 200
```

**Where It's Used:**
- **Line 822**: Cap for stake increases (prevents going over max)
- **Line 519**: Displayed in bot header

**Real-Time Example:**
```
✈️  AVIATOR BOT - ML MODE WITH ENHANCED LOGGING
💰 Stake: 50-200  ← Your max stake limit
```

---

### 3. **Stake Increase Percentage**

**How You Set It:**
```
Stake increase % (default 10): 15
```

**Where It's Used:**
- **Line 821**: Calculate new stake after wins
- **Formula**: `new_stake = current_stake × (1 + increase%/100)`

**Real-Time Example:**
```
Win with 50 stake
  → Next stake: 50 × 1.15 = 57.5 (rounded to 58)
Win with 58 stake
  → Next stake: 58 × 1.15 = 66.7 (rounded to 67)
```

---

### 4. **Cashout Delay (Seconds)**

**How You Set It:**
```
Cashout delay seconds (default 4.5): 5.0
```

**Where It's Used:**
- **Line 347**: Display in decision log
- **Line 680**: Countdown timer display
- **Line 691**: Calculate remaining time
- **Line 694**: Progress bar visualization
- **Line 700**: Crash detection comparison
- **Line 791**: Estimate final multiplier
- **Line 804, 813**: Record actual cashout time

**Real-Time Example:**
```
  ✅ DECISION: PLACE BET
  🎯 Target: 5.0s (~1.75x)  ← Your delay used here!

  ⏱️  CASHOUT COUNTDOWN - TARGET: 5.0s
  🟢 [████████████░░░░░░░░] 3.21s | SAFE  | ~1.45x  ← Counting to YOUR delay
```

---

### 5. **ML Confidence Threshold**

**How You Set It:**
```
ML threshold % (default 65.0): 70.0
```

**Where It's Used:**
- **Line 353**: Display in skip decision
- **Line 521**: Display in bot header
- **ML Signal Generator**: Decision logic (confidence >= threshold = BET)

**Real-Time Example:**
```
  ⏭️  DECISION: SKIP ROUND
  ❌ Reason: Ensemble confidence: 68.5%
  📊 Ensemble Confidence: 68.5% (Threshold: 70.0%)  ← Your threshold!
                                           ^^^^
```

**How It Affects Decisions:**
```python
if signal['confidence'] >= 70.0:  # Your threshold
    # Place bet
else:
    # Skip round
```

---

## Real-Time Configuration Display

### At Startup

```
📋 SUMMARY
════════════════════════════════════════════════
Initial stake:     50        ← You entered 50
Max stake:         200       ← You entered 200
Increase on win:   +15%      ← You entered 15
Cashout timing:    5.0s (~1.75x)  ← You entered 5.0
ML threshold:      70.0%     ← You entered 70.0
Balance tracking:  Enabled
════════════════════════════════════════════════
```

### During Operation

```
✈️  AVIATOR BOT - ML MODE WITH ENHANCED LOGGING
════════════════════════════════════════════════
💰 Stake: 50-200 | ⏱️  Cashout: 5.0s | 🎯 Threshold: 70.0%
                      ^^^^ Your value     ^^^^ Your value
════════════════════════════════════════════════
```

---

## Configuration Validation

### User Inputs Are Used Immediately

**Example Session:**
```bash
# User inputs
Initial stake: 100
Cashout delay: 6.0
ML threshold: 75.0

# Bot uses these values
Round #1: Confidence 72% → SKIP (< 75%)
Round #2: Confidence 78% → BET with 100 stake, cashout at 6.0s
Round #3: WIN → Next stake: 110 (100 + 10%)
```

### Dynamic Updates

Values are NOT hardcoded - they come from your input:

```python
# ❌ WRONG (hardcoded)
cashout_delay = 4.5

# ✅ CORRECT (from user)
cashout_delay = self.config_manager.cashout_delay  # Your input
```

---

## Verification Points

### Check Your Configuration Is Being Used

#### 1. **Check Stake**
Look for this in betting rounds:
```
💰 Setting stake: 50...  ← Should match your initial_stake
```

#### 2. **Check Cashout Timing**
Look for this in countdown:
```
⏱️  CASHOUT COUNTDOWN - TARGET: 5.0s  ← Should match your cashout_delay
```

#### 3. **Check Threshold**
Look for this in skip decisions:
```
📊 Ensemble Confidence: 68.5% (Threshold: 70.0%)  ← Should match your threshold
```

#### 4. **Check Stake Increase**
After a win, next round should show:
```
💰 Setting stake: 110...  ← Should be initial_stake × (1 + increase%)
```

---

## Configuration Persistence

### Saved to File

Your configuration is saved to `bot_config.json`:

```json
{
  "multiplier_region": [x, y, w, h],
  "initial_stake": 50,
  "max_stake": 200,
  "stake_increase_percent": 15,
  "cashout_delay": 5.0,
  ...
}
```

### Loaded on Restart

Next time you run the bot:
```
✓ Config loaded

Options:
  1. Use existing config  ← Uses your previous values
  2. New setup           ← Enter new values
```

---

## Advanced: Mid-Session Configuration

Currently, configuration is set at startup and cannot be changed mid-session. To change:

1. Stop bot (Ctrl+C)
2. Restart: `python bot_modular.py`
3. Choose "New setup" (Option 2)
4. Enter new values

**Future Enhancement**: Add `/config` command to change parameters during operation.

---

## Troubleshooting

### "Bot is not using my values!"

**Check These:**

1. **Verify you entered values correctly:**
   ```
   Initial stake (default 25): 50  ← Did you press Enter?
   ```

2. **Check Summary screen:**
   ```
   📋 SUMMARY
   Initial stake:     50  ← Does this match what you entered?
   ```

3. **Look for your values in logs:**
   ```
   💰 Setting stake: 50  ← Should match your input
   ```

4. **Check saved config:**
   ```bash
   cat bot_config.json
   # Look for your values in the file
   ```

### "Threshold not working!"

The threshold determines when to bet:

```
Confidence: 72% | Threshold: 75% → SKIP
Confidence: 78% | Threshold: 75% → BET
```

If you set threshold to 65% but bot keeps skipping:
- Models might have low confidence (<65%)
- Check model predictions in logs
- May need more training data

---

## Summary Table

| Parameter | User Input Location | Used In Code | Real-Time Effect |
|-----------|-------------------|--------------|------------------|
| Initial Stake | Line 1004-1007 | Line 591 | Amount bet each round |
| Max Stake | Line 1009-1011 | Line 822 | Cap for stake increases |
| Stake Increase % | Line 1013-1015 | Line 821 | Growth after wins |
| Cashout Delay | Line 1017-1019 | Lines 347, 680, 691, 694 | When to cashout |
| ML Threshold | Line 1021-1023 | Line 353, ML logic | When to bet vs skip |

---

## Code References

All configuration usage points:

```python
# Initial Stake
self.config_manager.initial_stake  # Lines 86, 559, 671, 730, 770, 863

# Max Stake
self.config_manager.max_stake  # Line 822

# Stake Increase %
self.config_manager.stake_increase_percent  # Line 821

# Cashout Delay
self.config_manager.cashout_delay  # Lines 347, 680, 691, 694, 700, 791, 804, 813

# ML Threshold
self.ml_generator.confidence_threshold  # Lines 353, 521, 1021, 1023
```

---

## Conclusion

✅ **All user configuration is actively used**
✅ **Values are applied in real-time**
✅ **No hardcoded defaults override your settings**
✅ **Configuration persists across restarts**
✅ **Every decision uses your parameters**

Your inputs directly control the bot's behavior! 🎯
