"""
Generate seasonal analysis reports
"""

def generate_seasonal_report(seasonal_analyzer):
    """Generate comprehensive seasonal analysis report."""
    
    hourly_stats = seasonal_analyzer.analyze_hourly_patterns()
    daily_stats = seasonal_analyzer.analyze_daily_patterns()
    current_context = seasonal_analyzer.get_current_context()
    
    report = f"""
📊 SEASONAL ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🕐 CURRENT CONTEXT:
• Time: {current_context['time_period']} ({current_context['hour']}:00)
• Day: {current_context['day_type']}
• Players: {current_context['player_count']} ({current_context['activity_level']} activity)

⏰ BEST HOURS (High Multiplier %):
"""
    
    # Sort hours by high multiplier percentage
    if hourly_stats:
        sorted_hours = sorted(hourly_stats.items(), 
                            key=lambda x: x[1]['high_count']/x[1]['total_rounds'], 
                            reverse=True)
        
        for hour, stats in sorted_hours[:5]:
            high_pct = (stats['high_count'] / stats['total_rounds']) * 100
            report += f"• {hour:02d}:00 - {high_pct:.1f}% high multipliers ({stats['total_rounds']} rounds)\n"
    
    report += "\n📅 BEST DAYS:\n"
    if daily_stats:
        sorted_days = sorted(daily_stats.items(), 
                           key=lambda x: x[1]['high_percentage'], 
                           reverse=True)
        
        for day, stats in sorted_days:
            report += f"• {day}: {stats['high_percentage']:.1f}% high multipliers\n"
    
    return report

if __name__ == "__main__":
    from datetime import datetime
    print("Seasonal report generator ready")