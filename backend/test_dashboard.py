"""
Quick Dashboard Test
Starts a test server with simulated data to verify dashboard functionality
"""

import os
import sys
import time
import random
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from flask_socketio import SocketIO

print("="*80)
print("  DASHBOARD TEST - Simulated Data Mode")
print("="*80)

# Initialize Flask app
app = Flask(__name__, template_folder='dashboard/templates')
socketio = SocketIO(app, cors_allowed_origins="*")

# Simulated data
round_number = 0
cumulative_profit = 0

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/advanced')
def advanced():
    return render_template('advanced_dashboard.html')

@app.route('/api/stats')
def get_stats():
    return {
        'stats': {
            'rounds_played': round_number,
            'rounds_observed': round_number,
            'ml_bets_placed': max(0, round_number - 5),
            'successful_cashouts': int(round_number * 0.65),
            'failed_cashouts': int(round_number * 0.35),
            'ml_skipped': 5,
            'total_bet': round_number * 50,
            'total_return': round_number * 52.5,
        },
        'current_stake': 50,
        'history': [],
        'cumulative_profit': cumulative_profit
    }

def simulate_round():
    """Simulate a game round with model predictions."""
    global round_number, cumulative_profit

    while True:
        time.sleep(5)  # New round every 5 seconds
        round_number += 1

        # Generate random multiplier
        mult = random.choice([
            random.uniform(1.0, 2.0),  # 50% chance low
            random.uniform(2.0, 5.0),  # 30% chance medium
            random.uniform(5.0, 10.0), # 15% chance high
            random.uniform(10.0, 50.0) # 5% chance spike
        ])

        # Generate model predictions (slightly off from actual)
        rf_pred = mult + random.uniform(-0.5, 0.5)
        gb_pred = mult + random.uniform(-0.4, 0.6)
        lgb_pred = mult + random.uniform(-0.6, 0.4)
        ensemble_pred = (rf_pred + gb_pred + lgb_pred) / 3

        # Calculate confidence
        confidence = random.uniform(55, 85)

        # Determine if bet was placed
        bet_placed = confidence >= 65 and random.random() > 0.3
        profit = 0

        if bet_placed:
            stake = 50
            cashout_target = 1.8
            if mult >= cashout_target:
                profit = stake * (cashout_target - 1)
                cumulative_profit += profit
            else:
                profit = -stake
                cumulative_profit += profit

        # Create round data
        round_data = {
            'timestamp': datetime.now().isoformat(),
            'multiplier': round(mult, 2),
            'bet_placed': bet_placed,
            'stake': 50 if bet_placed else 0,
            'cashout_time': 4.5 if bet_placed else 0,
            'profit_loss': round(profit, 2),
            'prediction': round(ensemble_pred, 2),
            'confidence': round(confidence, 1),
            'models': {
                'rf': round(rf_pred, 2),
                'gb': round(gb_pred, 2),
                'lgb': round(lgb_pred, 2)
            },
            'cumulative_profit': round(cumulative_profit, 2),
            'balance': 1000 + cumulative_profit,
            'stats': {
                'rounds_played': round_number,
                'rounds_observed': round_number,
                'ml_bets_placed': max(0, round_number - 5),
                'successful_cashouts': int(round_number * 0.65),
                'failed_cashouts': int(round_number * 0.35),
                'ml_skipped': 5,
                'total_bet': round_number * 50,
                'total_return': round_number * 52.5,
            },
            'current_stake': 50
        }

        # Emit to dashboard
        socketio.emit('round_update', round_data)
        print(f"Round {round_number}: {mult:.2f}x | Pred: {ensemble_pred:.2f}x | "
              f"Bet: {'Yes' if bet_placed else 'No'} | P/L: {cumulative_profit:+.2f}")

# Start background thread for simulated rounds
import threading
simulation_thread = threading.Thread(target=simulate_round, daemon=True)
simulation_thread.start()

print("\n✓ Test server starting...")
print("✓ Simulating game rounds every 5 seconds")
print("✓ Dashboard available at:")
print("  - Basic:    http://localhost:5000")
print("  - Advanced: http://localhost:5000/advanced")
print("\nPress Ctrl+C to stop\n")

try:
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
except KeyboardInterrupt:
    print("\n\nTest server stopped.")
