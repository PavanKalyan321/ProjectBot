"""
Selective Betting Strategy - Only bet on high-confidence patterns
"""

class SelectiveStrategy:
    """More selective betting strategy to reduce bet frequency."""
    
    def __init__(self, history_tracker):
        self.history_tracker = history_tracker
        
    def should_bet(self, recent_multipliers):
        """
        Selective betting logic - only bet on very strong patterns.
        
        Returns:
            dict: Betting decision with high selectivity
        """
        if len(recent_multipliers) < 20:
            return self._skip("Need 20+ rounds for analysis")
        
        last_10 = recent_multipliers[-10:]
        last_20 = recent_multipliers[-20:]
        
        # Pattern 1: Extreme cold streak (8+ low rounds in last 10)
        low_count = sum(1 for m in last_10 if m < 2.0)
        if low_count >= 8:
            return self._bet(2.5, 75, f"Extreme cold streak: {low_count}/10 rounds <2x")
        
        # Pattern 2: Post-burst opportunity (high mult followed by 5+ low)
        has_recent_burst = any(m >= 10.0 for m in last_10)
        if has_recent_burst:
            # Find position of highest multiplier
            burst_pos = None
            for i, m in enumerate(last_10):
                if m >= 10.0:
                    burst_pos = i
                    break
            
            # Check if followed by low multipliers
            if burst_pos is not None and burst_pos <= 4:  # Burst in first 5 rounds
                after_burst = last_10[burst_pos+1:]
                low_after_burst = sum(1 for m in after_burst if m < 2.5)
                if len(after_burst) >= 4 and low_after_burst >= 3:
                    return self._bet(2.0, 70, f"Post-burst pattern: {low_after_burst}/{len(after_burst)} low after {last_10[burst_pos]:.1f}x")
        
        # Pattern 3: Consistent medium range (looking for breakout)
        medium_count = sum(1 for m in last_10 if 2.0 <= m <= 3.5)
        if medium_count >= 7 and max(last_10) < 5.0:
            return self._bet(1.8, 65, f"Stable medium range: {medium_count}/10 rounds 2-3.5x")
        
        # Pattern 4: Long-term cold (15+ rounds without high multiplier)
        high_count_20 = sum(1 for m in last_20 if m >= 5.0)
        if high_count_20 == 0:
            avg_last_20 = sum(last_20) / len(last_20)
            if avg_last_20 < 2.5:
                return self._bet(3.0, 80, f"Long cold period: 0 high mults in 20 rounds, avg {avg_last_20:.1f}x")
        
        # Default: Skip (be very selective)
        return self._skip("No strong pattern detected")
    
    def _bet(self, target, confidence, reason):
        """Create bet signal."""
        return {
            'should_bet': True,
            'target_multiplier': target,
            'confidence': confidence,
            'reason': reason,
            'strategy': 'selective'
        }
    
    def _skip(self, reason):
        """Create skip signal."""
        return {
            'should_bet': False,
            'target_multiplier': 0,
            'confidence': 0,
            'reason': reason,
            'strategy': 'selective_skip'
        }