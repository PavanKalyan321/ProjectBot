"""
Seasonal Pattern Analyzer - Analyzes patterns by time, day, and player activity
"""

import time
from datetime import datetime, timedelta
from collections import defaultdict, deque

class SeasonalAnalyzer:
    """Analyze seasonal and player count patterns."""
    
    def __init__(self, history_tracker):
        self.history_tracker = history_tracker
        self.player_count_history = deque(maxlen=1000)
        self.hourly_stats = defaultdict(list)
        self.daily_stats = defaultdict(list)
        
    def capture_player_count(self):
        """Capture current player count (simulated - would need actual detection)."""
        # This would need screen capture of player count area
        # For now, simulate based on time patterns
        current_hour = datetime.now().hour
        
        # Simulate player count based on typical gaming patterns
        if 6 <= current_hour <= 10:  # Morning
            base_count = 150
        elif 11 <= current_hour <= 17:  # Afternoon  
            base_count = 300
        elif 18 <= current_hour <= 23:  # Evening (peak)
            base_count = 500
        else:  # Late night/early morning
            base_count = 80
            
        # Add weekend bonus
        if datetime.now().weekday() >= 5:  # Weekend
            base_count = int(base_count * 1.4)
            
        # Add some randomness
        import random
        player_count = base_count + random.randint(-50, 50)
        
        self.player_count_history.append({
            'timestamp': time.time(),
            'count': max(10, player_count),  # Minimum 10 players
            'hour': current_hour,
            'weekday': datetime.now().weekday()
        })
        
        return player_count
    
    def analyze_hourly_patterns(self):
        """Analyze multiplier patterns by hour of day."""
        recent_rounds = self.history_tracker.get_recent_rounds(500)
        if recent_rounds.empty:
            return {}
            
        hourly_data = defaultdict(list)
        
        for _, row in recent_rounds.iterrows():
            try:
                # Parse timestamp
                timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                hour = timestamp.hour
                multiplier = row['multiplier']
                
                hourly_data[hour].append(multiplier)
            except:
                continue
        
        # Calculate stats for each hour
        hourly_stats = {}
        for hour, multipliers in hourly_data.items():
            if len(multipliers) >= 5:  # Need minimum data
                hourly_stats[hour] = {
                    'avg_multiplier': sum(multipliers) / len(multipliers),
                    'high_count': sum(1 for m in multipliers if m >= 5.0),
                    'low_count': sum(1 for m in multipliers if m < 2.0),
                    'total_rounds': len(multipliers),
                    'volatility': self._calculate_volatility(multipliers)
                }
        
        return hourly_stats
    
    def analyze_daily_patterns(self):
        """Analyze patterns by day of week."""
        recent_rounds = self.history_tracker.get_recent_rounds(1000)
        if recent_rounds.empty:
            return {}
            
        daily_data = defaultdict(list)
        
        for _, row in recent_rounds.iterrows():
            try:
                timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                weekday = timestamp.weekday()  # 0=Monday, 6=Sunday
                multiplier = row['multiplier']
                
                daily_data[weekday].append(multiplier)
            except:
                continue
        
        # Calculate stats for each day
        daily_stats = {}
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day, multipliers in daily_data.items():
            if len(multipliers) >= 10:
                daily_stats[day_names[day]] = {
                    'avg_multiplier': sum(multipliers) / len(multipliers),
                    'high_count': sum(1 for m in multipliers if m >= 5.0),
                    'low_count': sum(1 for m in multipliers if m < 2.0),
                    'total_rounds': len(multipliers),
                    'high_percentage': (sum(1 for m in multipliers if m >= 5.0) / len(multipliers)) * 100
                }
        
        return daily_stats
    
    def analyze_player_count_correlation(self):
        """Analyze correlation between player count and multiplier patterns."""
        if len(self.player_count_history) < 50:
            return {'correlation': 'insufficient_data'}
        
        # Get recent multipliers with timestamps
        recent_rounds = self.history_tracker.get_recent_rounds(100)
        if recent_rounds.empty:
            return {'correlation': 'no_multiplier_data'}
        
        correlations = {
            'low_players_high_mult': 0,
            'high_players_low_mult': 0,
            'total_analyzed': 0
        }
        
        # Simple correlation analysis
        for _, row in recent_rounds.iterrows():
            try:
                round_time = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S').timestamp()
                multiplier = row['multiplier']
                
                # Find closest player count reading
                closest_player_data = min(
                    self.player_count_history,
                    key=lambda x: abs(x['timestamp'] - round_time)
                )
                
                player_count = closest_player_data['count']
                
                # Analyze patterns
                if player_count < 200 and multiplier >= 5.0:
                    correlations['low_players_high_mult'] += 1
                elif player_count > 400 and multiplier < 2.0:
                    correlations['high_players_low_mult'] += 1
                    
                correlations['total_analyzed'] += 1
                
            except:
                continue
        
        if correlations['total_analyzed'] > 0:
            correlations['low_players_high_mult_rate'] = (correlations['low_players_high_mult'] / correlations['total_analyzed']) * 100
            correlations['high_players_low_mult_rate'] = (correlations['high_players_low_mult'] / correlations['total_analyzed']) * 100
        
        return correlations
    
    def get_current_context(self):
        """Get current time and player context for decision making."""
        now = datetime.now()
        current_hour = now.hour
        current_weekday = now.weekday()
        
        # Capture current player count
        player_count = self.capture_player_count()
        
        # Determine time period
        if 6 <= current_hour <= 11:
            time_period = 'morning'
        elif 12 <= current_hour <= 17:
            time_period = 'afternoon'
        elif 18 <= current_hour <= 23:
            time_period = 'evening'
        else:
            time_period = 'night'
        
        # Determine day type
        if current_weekday < 5:
            day_type = 'weekday'
        else:
            day_type = 'weekend'
        
        # Player activity level
        if player_count < 150:
            activity_level = 'low'
        elif player_count < 350:
            activity_level = 'medium'
        else:
            activity_level = 'high'
        
        return {
            'hour': current_hour,
            'weekday': current_weekday,
            'time_period': time_period,
            'day_type': day_type,
            'player_count': player_count,
            'activity_level': activity_level
        }
    
    def get_seasonal_recommendation(self):
        """Get betting recommendation based on seasonal patterns."""
        context = self.get_current_context()
        hourly_stats = self.analyze_hourly_patterns()
        daily_stats = self.analyze_daily_patterns()
        
        recommendations = []
        confidence_boost = 0
        
        # Hour-based recommendations
        if context['hour'] in hourly_stats:
            hour_data = hourly_stats[context['hour']]
            if hour_data['high_count'] / hour_data['total_rounds'] > 0.15:  # >15% high multipliers
                recommendations.append(f"Good hour: {hour_data['high_count']}/{hour_data['total_rounds']} high multipliers")
                confidence_boost += 5
        
        # Day-based recommendations  
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        current_day_name = day_names[context['weekday']]
        
        if current_day_name in daily_stats:
            day_data = daily_stats[current_day_name]
            if day_data['high_percentage'] > 12:  # >12% high multipliers
                recommendations.append(f"Good day: {day_data['high_percentage']:.1f}% high multipliers")
                confidence_boost += 5
        
        # Player count recommendations
        if context['activity_level'] == 'low':
            recommendations.append("Low player count - potentially better odds")
            confidence_boost += 3
        elif context['activity_level'] == 'high':
            recommendations.append("High player count - more competitive")
            confidence_boost -= 2
        
        return {
            'context': context,
            'recommendations': recommendations,
            'confidence_boost': confidence_boost,
            'hourly_stats': hourly_stats,
            'daily_stats': daily_stats
        }
    
    def _calculate_volatility(self, multipliers):
        """Calculate volatility of multipliers."""
        if len(multipliers) < 2:
            return 0
        avg = sum(multipliers) / len(multipliers)
        variance = sum((x - avg) ** 2 for x in multipliers) / len(multipliers)
        return variance ** 0.5