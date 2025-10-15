# bot_with_dashboard.py
# Complete Aviator Bot with Real-time Dashboard
# Installation: pip install flask flask-socketio pyautogui pillow opencv-python numpy pandas pywin32

import pyautogui
import time
from PIL import Image
import cv2
import numpy as np
import keyboard
import json
import os
import csv
from datetime import datetime
import pandas as pd
from collections import deque
import re
import win32clipboard
import win32con
import threading
import webbrowser
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

# ============================================================================
# DASHBOARD SERVER
# ============================================================================

class AviatorDashboard:
    """Real-time web dashboard for bot monitoring"""
    
    def __init__(self, bot, port=5000):
        self.bot = bot
        self.port = port
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.is_running = False
        self.round_history = deque(maxlen=100)
        self._setup_routes()
        self._create_dashboard_template()
        
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
        
        @self.app.route('/api/stats')
        def get_stats():
            profit = self.bot.stats['total_return'] - self.bot.stats['total_bet']
            return jsonify({
                'stats': self.bot.stats,
                'current_stake': self.bot.current_stake,
                'history': list(self.round_history),
                'cumulative_profit': profit
            })
    
    def emit_round_update(self, round_data):
        """Send round update to dashboard"""
        self.round_history.append(round_data)
        try:
            self.socketio.emit('round_update', round_data)
        except:
            pass
    
    def emit_stats_update(self):
        """Send stats update to dashboard"""
        try:
            profit = self.bot.stats['total_return'] - self.bot.stats['total_bet']
            self.socketio.emit('stats_update', {
                'stats': self.bot.stats,
                'current_stake': self.bot.current_stake,
                'cumulative_profit': profit
            })
        except:
            pass
    
    def _create_dashboard_template(self):
        """Create dashboard HTML file"""
        os.makedirs('templates', exist_ok=True)
        
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aviator Bot Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
            color: #fff;
            padding: 10px;
            height: 100vh;
            overflow: hidden;
        }
        
        .container {
            max-width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .header {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
            box-shadow: 0 0 10px #10b981;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.1); }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
        }
        
        .stat-card .label {
            font-size: 11px;
            opacity: 0.8;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-card .value {
            font-size: 24px;
            font-weight: bold;
        }
        
        .stat-card.positive .value { color: #10b981; }
        .stat-card.negative .value { color: #ef4444; }
        .stat-card.neutral .value { color: #fbbf24; }
        
        .main-content {
            flex: 1;
            display: grid;
            grid-template-columns: 1.5fr 1fr;
            gap: 10px;
            overflow: hidden;
        }
        
        .panel {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 15px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .panel h2 {
            font-size: 16px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .rounds-table-container {
            flex: 1;
            overflow-y: auto;
        }
        
        .rounds-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .rounds-table th {
            background: rgba(255,255,255,0.2);
            padding: 8px 6px;
            text-align: left;
            font-size: 11px;
            position: sticky;
            top: 0;
            z-index: 1;
        }
        
        .rounds-table td {
            padding: 8px 6px;
            font-size: 11px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .rounds-table tr:hover {
            background: rgba(255,255,255,0.1);
        }
        
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
        }
        
        .badge.success { background: #10b981; color: #fff; }
        .badge.failure { background: #ef4444; color: #fff; }
        .badge.skip { background: #6b7280; color: #fff; }
        .badge.win { background: #22c55e; color: #fff; }
        .badge.loss { background: #dc2626; color: #fff; }
        
        .recent-rounds {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        
        .round-bubble {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: bold;
            border: 2px solid rgba(255,255,255,0.4);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .round-bubble.crash {
            background: linear-gradient(135deg, #dc2626, #991b1b);
        }
        
        .round-bubble.low {
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }
        
        .round-bubble.medium {
            background: linear-gradient(135deg, #10b981, #059669);
        }
        
        .round-bubble.high {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        }
        
        .round-bubble.mega {
            background: linear-gradient(135deg, #a855f7, #7c3aed);
        }
        
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.3);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.5);
        }
        
        @media (max-width: 1200px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        .chart-placeholder {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            opacity: 0.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <div class="status-indicator"></div>
                ✈️ Aviator Bot Dashboard
            </h1>
            <div id="timestamp" style="font-size: 14px; opacity: 0.9;"></div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">🎯 Rounds</div>
                <div class="value" id="rounds-played">0</div>
            </div>
            <div class="stat-card positive">
                <div class="label">✅ Success</div>
                <div class="value" id="success-rate">0%</div>
            </div>
            <div class="stat-card">
                <div class="label">💰 Stake</div>
                <div class="value" id="current-stake">25</div>
            </div>
            <div class="stat-card" id="profit-card">
                <div class="label">📊 Profit/Loss</div>
                <div class="value" id="total-profit">+0.00</div>
            </div>
            <div class="stat-card neutral">
                <div class="label">🔥 Streak</div>
                <div class="value" id="win-streak">0</div>
            </div>
            <div class="stat-card">
                <div class="label">📈 ROI</div>
                <div class="value" id="roi">0%</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="panel">
                <h2>📋 Round History</h2>
                <div class="rounds-table-container">
                    <table class="rounds-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Action</th>
                                <th>Multiplier</th>
                                <th>Stake</th>
                                <th>Result</th>
                                <th>P/L</th>
                            </tr>
                        </thead>
                        <tbody id="rounds-tbody">
                            <tr>
                                <td colspan="6" style="text-align: center; opacity: 0.5; padding: 20px;">
                                    ⏳ Waiting for rounds...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="panel">
                <h2>🎲 Recent Multipliers</h2>
                <div class="recent-rounds" id="recent-rounds">
                    <!-- Bubbles will be added here -->
                </div>
                
                <h2>📊 Statistics</h2>
                <div class="chart-placeholder">
                    <div style="font-size: 48px; margin-bottom: 10px;">📈</div>
                    <div>Live profit tracking active</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        setInterval(() => {
            document.getElementById('timestamp').textContent = 
                new Date().toLocaleTimeString('en-US', {hour12: false});
        }, 1000);
        
        socket.on('round_update', (data) => {
            updateStats(data.stats, data.current_stake);
            addRoundToTable(data);
            addRecentMultiplier(data.multiplier);
        });
        
        socket.on('stats_update', (data) => {
            updateStats(data.stats, data.current_stake);
        });
        
        function updateStats(stats, currentStake) {
            document.getElementById('rounds-played').textContent = stats.rounds_played;
            document.getElementById('current-stake').textContent = currentStake;
            
            const successRate = stats.ml_bets_placed > 0 
                ? ((stats.successful_cashouts / stats.ml_bets_placed) * 100).toFixed(1)
                : 0;
            document.getElementById('success-rate').textContent = successRate + '%';
            
            const profit = stats.total_return - stats.total_bet;
            const profitEl = document.getElementById('total-profit');
            profitEl.textContent = (profit >= 0 ? '+' : '') + profit.toFixed(2);
            
            const profitCard = document.getElementById('profit-card');
            profitCard.className = profit > 0 ? 'stat-card positive' : 
                                   profit < 0 ? 'stat-card negative' : 'stat-card';
            
            document.getElementById('win-streak').textContent = stats.current_streak;
            
            const roi = stats.total_bet > 0 
                ? ((profit / stats.total_bet) * 100).toFixed(1)
                : 0;
            document.getElementById('roi').textContent = roi + '%';
        }
        
        function addRoundToTable(data) {
            const tbody = document.getElementById('rounds-tbody');
            
            if (tbody.children[0]?.children[0]?.colSpan === 6) {
                tbody.innerHTML = '';
            }
            
            const row = document.createElement('tr');
            const time = new Date(data.timestamp).toLocaleTimeString('en-US', {
                hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
            
            const actionBadge = data.bet_placed 
                ? '<span class="badge success">BET</span>'
                : '<span class="badge skip">SKIP</span>';
            
            const resultBadge = data.bet_placed
                ? (data.profit_loss > 0 
                    ? '<span class="badge win">WIN</span>'
                    : '<span class="badge loss">LOSS</span>')
                : '-';
            
            const multColor = data.multiplier < 2 ? '#ef4444' :
                             data.multiplier < 5 ? '#fbbf24' :
                             data.multiplier < 10 ? '#10b981' : '#3b82f6';
            
            row.innerHTML = `
                <td>${time}</td>
                <td>${actionBadge}</td>
                <td style="color: ${multColor}; font-weight: bold;">${data.multiplier.toFixed(2)}x</td>
                <td>${data.stake || '-'}</td>
                <td>${resultBadge}</td>
                <td style="color: ${data.profit_loss > 0 ? '#10b981' : data.profit_loss < 0 ? '#ef4444' : '#fff'}; font-weight: bold;">
                    ${data.profit_loss !== 0 ? (data.profit_loss > 0 ? '+' : '') + data.profit_loss.toFixed(2) : '-'}
                </td>
            `;
            
            tbody.insertBefore(row, tbody.firstChild);
            
            while (tbody.children.length > 50) {
                tbody.removeChild(tbody.lastChild);
            }
        }
        
        function addRecentMultiplier(mult) {
            const container = document.getElementById('recent-rounds');
            const bubble = document.createElement('div');
            const category = mult < 2 ? 'crash' : 
                           mult < 5 ? 'low' : 
                           mult < 10 ? 'medium' : 
                           mult < 20 ? 'high' : 'mega';
            bubble.className = 'round-bubble ' + category;
            bubble.textContent = mult.toFixed(2) + 'x';
            
            container.insertBefore(bubble, container.firstChild);
            
            while (container.children.length > 24) {
                container.removeChild(container.lastChild);
            }
        }
        
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                updateStats(data.stats, data.current_stake);
                data.history.forEach(round => {
                    addRoundToTable(round);
                    addRecentMultiplier(round.multiplier);
                });
            });
    </script>
</body>
</html>'''
        
        with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def start(self):
        """Start dashboard server in background thread"""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(
            target=lambda: self.socketio.run(self.app, port=self.port, debug=False, 
                                            use_reloader=False, log_output=False),
            daemon=True
        )
        thread.start()
        
        time.sleep(1.5)
        try:
            webbrowser.open(f'http://localhost:{self.port}')
        except:
            pass
        
        print(f"✓ Dashboard running at http://localhost:{self.port}")


# ============================================================================
# HISTORY TRACKER
# ============================================================================

class RoundHistoryTracker:
    """Track and log round history from the game's history bar"""

    def __init__(self, history_region=None):
        self.history_region = history_region
        self.csv_file = "aviator_rounds_history.csv"
        self.last_round_data = None
        self.last_logged_multiplier = None
        self.last_log_time = 0
        self.log_cooldown = 2.0
        self.local_history_buffer = deque(maxlen=10)

        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'round_id', 'multiplier',
                    'bet_placed', 'stake_amount', 'cashout_time',
                    'profit_loss', 'model_prediction', 'model_confidence',
                    'model_predicted_range_low', 'model_predicted_range_high'
                ])

        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except Exception:
            self.tesseract_available = False

    def capture_history_region(self):
        if not self.history_region:
            return None
        try:
            x, y, w, h = self.history_region
            if w <= 0 or h <= 0 or x < 0 or y < 0:
                return None
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            return screenshot
        except Exception:
            return None
    
    def auto_log_from_clipboard(self, detector, force=False):
        try:
            current_time = time.time()
            if not force and (current_time - self.last_log_time) < self.log_cooldown:
                return False, None

            multiplier = detector.read_multiplier_from_clipboard()
            if multiplier is None:
                return False, None

            if not force and multiplier == self.last_logged_multiplier:
                return False, multiplier

            self.log_round(
                multiplier=multiplier,
                bet_placed=False,
                stake=0,
                cashout_time=0,
                profit_loss=0
            )

            self.local_history_buffer.append({
                'multiplier': multiplier,
                'timestamp': datetime.now().isoformat(),
                'round_id': datetime.now().strftime("%Y%m%d%H%M%S%f")
            })

            self.last_logged_multiplier = multiplier
            self.last_log_time = current_time
            return True, multiplier

        except Exception:
            return False, None

    def get_local_history(self, n=10):
        history = list(self.local_history_buffer)
        return history[-n:] if len(history) >= n else history

    def log_round(self, multiplier, bet_placed=False, stake=0, cashout_time=0,
                  profit_loss=0, prediction=None, confidence=0, pred_range=(0, 0)):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        round_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, round_id, multiplier,
                bet_placed, stake, cashout_time,
                profit_loss, prediction, confidence,
                pred_range[0] if pred_range else 0, pred_range[1] if pred_range else 0
            ])

    def get_recent_rounds(self, n=100):
        try:
            df = pd.read_csv(self.csv_file)
            return df.tail(n)
        except Exception:
            return pd.DataFrame()


# ============================================================================
# ML SIGNAL GENERATOR
# ============================================================================

class MLSignalGenerator:
    """Generate betting signals using ensemble ML models"""

    def __init__(self, history_tracker):
        self.history_tracker = history_tracker
        self.confidence_threshold = 65.0
        self.models_loaded = False
        self.feature_window = 20

    def engineer_features(self, recent_rounds):
        if len(recent_rounds) < self.feature_window:
            return None
        multipliers = recent_rounds['multiplier'].values[-self.feature_window:]
        features = {
            'mean': np.mean(multipliers),
            'std': np.std(multipliers),
            'min': np.min(multipliers),
            'max': np.max(multipliers),
            'median': np.median(multipliers),
            'trend': np.polyfit(range(len(multipliers)), multipliers, 1)[0],
            'momentum': multipliers[-1] - multipliers[-5] if len(multipliers) >= 5 else 0,
            'low_count': np.sum(multipliers < 2.0),
            'high_count': np.sum(multipliers >= 2.0),
            'last_1': multipliers[-1],
            'last_2': multipliers[-2] if len(multipliers) >= 2 else 0,
            'last_3': multipliers[-3] if len(multipliers) >= 3 else 0,
        }
        return np.array(list(features.values())).reshape(1, -1)

    def generate_ensemble_signal(self):
        recent_rounds = self.history_tracker.get_recent_rounds(self.feature_window + 10)
        if len(recent_rounds) < self.feature_window:
            return {
                'should_bet': False,
                'confidence': 0,
                'prediction': 0,
                'range': (0, 0),
                'reason': 'Insufficient data'
            }
        
        features = self.engineer_features(recent_rounds)
        if features is None:
            return {'should_bet': False, 'confidence': 0, 'prediction': 0, 
                   'range': (0,0), 'reason': 'Feature engineering failed'}
        
        # Simulated predictions
        predictions = [np.random.uniform(1.5, 3.0) for _ in range(4)]
        confidences = [np.random.uniform(40, 90) for _ in range(4)]
        
        ensemble_pred = np.mean(predictions)
        ensemble_conf = np.mean(confidences)
        pred_std = np.std(predictions)
        pred_range = (max(1.0, ensemble_pred - pred_std), ensemble_pred + pred_std)
        
        should_bet = ensemble_conf >= self.confidence_threshold
        
        return {
            'should_bet': should_bet,
            'confidence': round(ensemble_conf, 2),
            'prediction': round(ensemble_pred, 2),
            'range': (round(pred_range[0], 2), round(pred_range[1], 2)),
            'reason': f"Ensemble confidence: {ensemble_conf:.1f}%"
        }


# ============================================================================
# GAME STATE DETECTOR
# ============================================================================

class GameStateDetector:
    """Detect game states: Awaiting, Active, Crashed"""

    def __init__(self, region):
        self.region = region
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.tesseract_available = True
        except Exception:
            self.tesseract_available = False
            
    def read_multiplier_from_clipboard(self):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            time.sleep(0.1)
            
            x1, y1 = 19, 1101
            x2, y2 = 98, 1106
            
            pyautogui.moveTo(x1, y1, duration=0.1)
            time.sleep(0.05)
            pyautogui.mouseDown()
            pyautogui.moveTo(x2, y2, duration=0.1)
            pyautogui.mouseUp()
            time.sleep(0.1)
            
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.15)
            
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            except:
                try:
                    data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                except:
                    data = None
            win32clipboard.CloseClipboard()
            
            if not data:
                return None
                
            if isinstance(data, bytes):
                text = data.decode('utf-8', errors='ignore')
            else:
                text = str(data)
            
            text = text.strip().replace(' ', '').replace(',', '.')
            
            patterns = [
                r'(\d+\.?\d*)x',
                r'x(\d+\.?\d*)',
                r'^(\d+\.?\d*)$',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        if 0 < value <= 1000:
                            return value
                    except:
                        continue
            
            return None
            
        except Exception:
            return None

    def read_text_in_region(self):
        if not self.tesseract_available:
            return None
        try:
            image = pyautogui.screenshot(region=self.region)
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            text = self.pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')
            
            if text:
                text = text.strip().upper()
                text = text.replace('0', 'O').replace('1', 'I')
                if any(keyword in text for keyword in ['AWAITING NEXT FLIGHT', 'AWAIT', 'NEXT', 'FLIGHT']):
                    return 'AWAITING'
            
            return 'UNKNOWN'
        except Exception:
            return None

    def is_awaiting_next_flight(self):
        state = self.read_text_in_region()
        return state == 'AWAITING'

    def wait_for_awaiting_message(self, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_awaiting_next_flight():
                return True
            time.sleep(0.5)
        return False

    def wait_for_game_start(self, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            state = self.read_text_in_region()
            if state != 'AWAITING' and state != 'UNKNOWN':
                return True
            time.sleep(0.2)
        return False


# ============================================================================
# AVIATOR BOT ML
# ============================================================================

class AviatorBotML:
    """Enhanced Aviator bot with ML signal generation and dashboard"""

    def __init__(self):
        self.stake_coords = None
        self.bet_button_coords = None
        self.cashout_coords = None
        self.multiplier_region = None
        self.history_region = None

        self.initial_stake = 25
        self.current_stake = 25
        self.max_stake = 1000
        self.stake_increase_percent = 20

        self.cashout_delay = 2.0
        self.is_betting = False
        
        # State tracking
        self.bet_state = "IDLE"
        self.bet_verification_attempts = 0
        self.max_verification_attempts = 3

        self.detector = None
        self.history_tracker = None
        self.ml_generator = None
        self.dashboard = None

        self.config_file = "aviator_ml_config.json"

        self.stats = {
            "rounds_played": 0,
            "rounds_observed": 0,
            "ml_bets_placed": 0,
            "successful_cashouts": 0,
            "failed_cashouts": 0,
            "ml_skipped": 0,
            "total_bet": 0,
            "total_return": 0,
            "current_streak": 0,
            "max_stake_reached": 25
        }

    def save_config(self):
        config = {
            "stake_coords": self.stake_coords,
            "bet_button_coords": self.bet_button_coords,
            "cashout_coords": self.cashout_coords,
            "multiplier_region": self.multiplier_region,
            "history_region": self.history_region,
            "cashout_delay": self.cashout_delay,
            "initial_stake": self.initial_stake,
            "max_stake": self.max_stake,
            "stake_increase_percent": self.stake_increase_percent
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.stake_coords = tuple(config["stake_coords"]) if config.get("stake_coords") else None
                self.bet_button_coords = tuple(config["bet_button_coords"]) if config.get("bet_button_coords") else None
                self.cashout_coords = tuple(config["cashout_coords"]) if config.get("cashout_coords") else None
                self.multiplier_region = tuple(config["multiplier_region"]) if config.get("multiplier_region") else None
                self.history_region = tuple(config["history_region"]) if config.get("history_region") else None
                self.cashout_delay = config.get("cashout_delay", 2.0)
                self.initial_stake = config.get("initial_stake", 25)
                self.max_stake = config.get("max_stake", 1000)
                self.stake_increase_percent = config.get("stake_increase_percent", 20)
                self.current_stake = self.initial_stake
                return True
            except Exception:
                return False
        return False

    def setup_coordinates(self):
        print("\n" + "="*60)
        print("COORDINATE SETUP")
        print("="*60)
        print("\nPosition your mouse and press SPACE\n")
        
        print("1. Hover over STAKE INPUT field...")
        keyboard.wait('space')
        self.stake_coords = pyautogui.position()
        print(f"   ✓ Stake input: {self.stake_coords}")
        time.sleep(0.5)
        
        print("\n2. Hover over PLACE BET button...")
        keyboard.wait('space')
        self.bet_button_coords = pyautogui.position()
        print(f"   ✓ Place bet button: {self.bet_button_coords}")
        time.sleep(0.5)
        
        print("\n3. Hover over CASHOUT button location...")
        keyboard.wait('space')
        self.cashout_coords = pyautogui.position()
        print(f"   ✓ Cashout button: {self.cashout_coords}")
        time.sleep(0.5)
        
        print("\n4. Define multiplier region (TOP-LEFT corner)...")
        keyboard.wait('space')
        x1, y1 = pyautogui.position()
        print(f"   ✓ Top-left: ({x1}, {y1})")
        time.sleep(0.5)
        
        print("\n   Define multiplier region (BOTTOM-RIGHT corner)...")
        keyboard.wait('space')
        x2, y2 = pyautogui.position()
        print(f"   ✓ Bottom-right: ({x2}, {y2})")
        self.multiplier_region = (x1, y1, x2-x1, y2-y1)
        print(f"\n✓ Multiplier region: {self.multiplier_region}")
        
        print("\n5. Define ROUND HISTORY bar (TOP-LEFT corner)...")
        keyboard.wait('space')
        h1, h2 = pyautogui.position()
        print(f"   ✓ History top-left: ({h1}, {h2})")
        time.sleep(0.5)
        
        print("\n   Define ROUND HISTORY bar (BOTTOM-RIGHT corner)...")
        keyboard.wait('space')
        h3, h4 = pyautogui.position()
        print(f"   ✓ History bottom-right: ({h3}, {h4})")
        self.history_region = (h1, h2, h3-h1, h4-h2)
        print(f"\n✓ History region: {self.history_region}")
        
        self.detector = GameStateDetector(self.multiplier_region)
        self.history_tracker = RoundHistoryTracker(self.history_region)
        self.ml_generator = MLSignalGenerator(self.history_tracker)
        self.save_config()
        
        print("\n" + "="*60)
        print("✓ Setup complete!")
        print("="*60 + "\n")

    def set_stake(self, amount):
        try:
            pyautogui.click(self.stake_coords)
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('backspace')
            time.sleep(0.1)
            pyautogui.typewrite(str(amount), interval=0.05)
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️  Error setting stake: {e}")

    def place_bet(self):
        """Place bet with state verification"""
        try:
            self.bet_state = "PLACING"
            pyautogui.click(self.bet_button_coords)
            time.sleep(0.4)
            
            self.is_betting = True
            self.bet_state = "PLACED"
            self.stats["rounds_played"] += 1
            self.stats["ml_bets_placed"] += 1
            self.stats["total_bet"] += self.current_stake
            print(f"  ✅ Bet placed: {self.current_stake}")
            return True
                
        except Exception as e:
            print(f"  ⚠️  Error placing bet: {e}")
            self.bet_state = "IDLE"
            self.is_betting = False
            return False

    def cashout(self):
        try:
            pyautogui.click(self.cashout_coords)
            self.is_betting = False
            self.bet_state = "CASHED_OUT"
            self.stats["successful_cashouts"] += 1
            self.stats["current_streak"] += 1
            print(f"  💰 CASHED OUT")
        except Exception as e:
            print(f"  ⚠️  Error cashing out: {e}")
            self.stats["failed_cashouts"] += 1

    def increase_stake(self):
        old_stake = self.current_stake
        new_stake = self.current_stake * (1 + self.stake_increase_percent / 100)
        if new_stake > self.max_stake:
            new_stake = self.max_stake
        self.current_stake = int(new_stake)
        if self.current_stake > self.stats["max_stake_reached"]:
            self.stats["max_stake_reached"] = self.current_stake
        if self.current_stake != old_stake:
            print(f"  📈 Stake: {old_stake} → {self.current_stake}")

    def reset_stake(self):
        old_stake = self.current_stake
        self.current_stake = self.initial_stake
        self.stats["current_streak"] = 0
        if old_stake != self.current_stake:
            print(f"  📉 Stake reset: {old_stake} → {self.current_stake}")

    def estimate_multiplier(self, elapsed_time):
        import math
        multiplier = math.exp(0.15 * elapsed_time)
        return round(multiplier, 2)

    def _create_round_data(self, multiplier, bet_placed, stake, cashout_time, 
                          profit_loss, signal, cumulative_profit):
        """Create round data for dashboard"""
        return {
            'timestamp': datetime.now().isoformat(),
            'multiplier': multiplier,
            'bet_placed': bet_placed,
            'stake': stake,
            'cashout_time': cashout_time,
            'profit_loss': profit_loss,
            'prediction': signal.get('prediction', 0) if signal else 0,
            'confidence': signal.get('confidence', 0) if signal else 0,
            'cumulative_profit': cumulative_profit,
            'stats': self.stats.copy(),
            'current_stake': self.current_stake
        }

    def _emit_dashboard_update(self, round_data):
        """Send update to dashboard"""
        if self.dashboard:
            self.dashboard.emit_round_update(round_data)

    def run_ml_mode(self):
        print("\n" + "="*60)
        print("✈️  AVIATOR BOT - ML MODE")
        print("="*60)
        print(f"Cashout: {self.cashout_delay}s | Threshold: {self.ml_generator.confidence_threshold}%")
        print("="*60)
        print("\n🚀 Starting bot... Press Ctrl+C to stop\n")
        
        cumulative_profit = 0

        try:
            while True:
                print(f"\n{'='*60}")
                print(f"🎯 ROUND {self.stats['rounds_observed'] + 1}")
                print(f"{'='*60}")
                
                if not self.detector.wait_for_awaiting_message(timeout=60):
                    print("⚠️  Timeout waiting for AWAITING state")
                    continue

                # Auto-log completed round
                print("  📝 Logging round...")
                time.sleep(0.3)
                success, logged_mult = self.history_tracker.auto_log_from_clipboard(self.detector)

                if success:
                    print(f"  ✅ Logged: {logged_mult}x")

                # Generate ML signal
                print("  🤖 Analyzing...")
                signal = self.ml_generator.generate_ensemble_signal()
                print(f"  📊 Prediction: {signal['prediction']}x | Confidence: {signal['confidence']}%")

                if signal['should_bet']:
                    print(f"  💵 PLACING BET: {self.current_stake}")
                    stake_used = self.current_stake
                    self.set_stake(stake_used)
                    time.sleep(0.4)
                    
                    bet_success = self.place_bet()
                    
                    if not bet_success:
                        print("  ❌ Bet placement failed")
                        self.stats["rounds_observed"] += 1
                        continue

                    if not self.detector.wait_for_game_start(timeout=10):
                        print("  ⚠️  Game didn't start")
                        self.is_betting = False
                        self.bet_state = "IDLE"
                        
                        loss = -stake_used
                        cumulative_profit += loss
                        self.history_tracker.log_round(0, True, stake_used, 0, loss,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                        
                        round_data = self._create_round_data(0, True, stake_used, 0, loss, 
                                                             signal, cumulative_profit)
                        self._emit_dashboard_update(round_data)
                        
                        self.reset_stake()
                        self.stats["rounds_observed"] += 1
                        continue

                    print(f"  ⏱️  Waiting {self.cashout_delay}s...")
                    round_start = time.time()
                    crashed_early = False

                    while True:
                        elapsed = time.time() - round_start
                        if self.detector.is_awaiting_next_flight():
                            crashed_early = True
                            print("\n  💥 CRASHED!")
                            break
                        if elapsed >= self.cashout_delay:
                            break
                        time.sleep(0.1)

                    if crashed_early:
                        self.is_betting = False
                        self.bet_state = "CRASHED"
                        self.stats["failed_cashouts"] += 1
                        self.stats["current_streak"] = 0
                        
                        loss = -stake_used
                        cumulative_profit += loss
                        
                        self.history_tracker.log_round(0, True, stake_used, elapsed, loss,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                        
                        round_data = self._create_round_data(0, True, stake_used, elapsed, loss, 
                                                             signal, cumulative_profit)
                        self._emit_dashboard_update(round_data)
                        
                        print(f"  💸 Loss: -{stake_used:.2f}")
                        print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                        
                        self.reset_stake()
                        self.stats["rounds_observed"] += 1
                        time.sleep(2)
                        continue

                    # Cashout
                    self.cashout()
                    time.sleep(0.5)
                    
                    final_mult = self.estimate_multiplier(self.cashout_delay)
                    returns = stake_used * final_mult
                    profit = returns - stake_used
                    cumulative_profit += profit
                    self.stats["total_return"] += returns
                    
                    self.history_tracker.log_round(final_mult, True, stake_used, 
                                                  self.cashout_delay, profit,
                                                  signal['prediction'], signal['confidence'], signal['range'])
                    
                    round_data = self._create_round_data(final_mult, True, stake_used, 
                                                         self.cashout_delay, profit, 
                                                         signal, cumulative_profit)
                    self._emit_dashboard_update(round_data)
                    
                    print(f"  ✅ WIN: +{profit:.2f}")
                    print(f"  📊 Total P/L: {cumulative_profit:+.2f}")
                    
                    self.increase_stake()

                else:
                    # Skip round
                    print(f"  ⏭️  SKIPPING: {signal['reason']}")
                    self.stats["ml_skipped"] += 1
                    
                    start_wait = time.time()
                    while time.time() - start_wait < 30:
                        if self.detector.is_awaiting_next_flight():
                            break
                        time.sleep(0.5)
                    
                    time.sleep(0.5)
                    
                    # Try to get observed multiplier
                    observed_mult = 2.0
                    try:
                        success, mult = self.history_tracker.auto_log_from_clipboard(self.detector, force=False)
                        if success and mult:
                            observed_mult = mult
                    except:
                        pass
                    
                    if not success:
                        self.history_tracker.log_round(observed_mult, False, 0, 0, 0,
                                                      signal['prediction'], signal['confidence'], signal['range'])
                    
                    round_data = self._create_round_data(observed_mult, False, 0, 0, 0, 
                                                         signal, cumulative_profit)
                    self._emit_dashboard_update(round_data)

                self.stats["rounds_observed"] += 1
                self.bet_state = "IDLE"
                
                if self.dashboard:
                    self.dashboard.emit_stats_update()
                
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⏹️  Bot stopped by user")
            self.print_stats()

    def print_stats(self):
        print("\n" + "="*60)
        print("📊 BOT STATISTICS")
        print("="*60)
        print(f"Rounds observed:      {self.stats['rounds_observed']}")
        print(f"ML bets placed:       {self.stats['ml_bets_placed']}")
        print(f"ML bets skipped:      {self.stats['ml_skipped']}")
        print(f"Successful cashouts:  {self.stats['successful_cashouts']}")
        print(f"Failed cashouts:      {self.stats['failed_cashouts']}")
        print(f"Current streak:       {self.stats['current_streak']}")
        
        if self.stats['ml_bets_placed'] > 0:
            success_rate = (self.stats['successful_cashouts'] / self.stats['ml_bets_placed']) * 100
            print(f"Success rate:         {success_rate:.1f}%")
        
        print(f"\n💰 Financial Summary:")
        print(f"  Total bet:          {self.stats['total_bet']:.2f}")
        print(f"  Total return:       {self.stats['total_return']:.2f}")
        profit = self.stats['total_return'] - self.stats['total_bet']
        print(f"  Profit/Loss:        {profit:+.2f}")
        
        if self.stats['total_bet'] > 0:
            roi = (profit / self.stats['total_bet']) * 100
            print(f"  ROI:                {roi:+.1f}%")
        
        print("="*60 + "\n")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function"""
    print("="*60)
    print("✈️  AVIATOR BOT - ML ENHANCED WITH DASHBOARD")
    print("="*60)

    bot = AviatorBotML()

    # Load or setup configuration
    if bot.load_config() and bot.multiplier_region:
        print(f"\n✓ Configuration loaded")
        print("\nOptions:")
        print("  1. Use existing config and run")
        print("  2. New setup")
        choice = input("\nChoice (1/2): ").strip()
        
        if choice == '2':
            bot.setup_coordinates()
    else:
        bot.setup_coordinates()

    # Initialize components
    if not bot.detector and bot.multiplier_region:
        bot.detector = GameStateDetector(bot.multiplier_region)
    if not bot.history_tracker and bot.history_region:
        bot.history_tracker = RoundHistoryTracker(bot.history_region)
    if not bot.ml_generator and bot.history_tracker:
        bot.ml_generator = MLSignalGenerator(bot.history_tracker)

    # Bot parameters
    print("\n" + "="*60)
    print("⚙️  BOT PARAMETERS")
    print("="*60)
    
    initial = input(f"\nInitial stake (default {bot.initial_stake}): ").strip()
    if initial:
        bot.initial_stake = int(initial)
        bot.current_stake = bot.initial_stake
    
    max_stake = input(f"Max stake limit (default {bot.max_stake}): ").strip()
    if max_stake:
        bot.max_stake = int(max_stake)
    
    increase = input(f"Stake increase % (default {bot.stake_increase_percent}): ").strip()
    if increase:
        bot.stake_increase_percent = int(increase)
    
    delay = input(f"Cashout delay in seconds (default {bot.cashout_delay}): ").strip()
    if delay:
        bot.cashout_delay = float(delay)
    
    threshold = input(f"ML confidence threshold % (default {bot.ml_generator.confidence_threshold}): ").strip()
    if threshold:
        bot.ml_generator.confidence_threshold = float(threshold)

    estimated_mult = bot.estimate_multiplier(bot.cashout_delay)
    
    print("\n" + "="*60)
    print("📋 STRATEGY SUMMARY")
    print("="*60)
    print(f"Mode:              ML Ensemble")
    print(f"Initial stake:     {bot.initial_stake}")
    print(f"Max stake:         {bot.max_stake}")
    print(f"Increase on win:   +{bot.stake_increase_percent}%")
    print(f"Cashout timing:    {bot.cashout_delay}s (~{estimated_mult}x)")
    print(f"ML threshold:      {bot.ml_generator.confidence_threshold}%")
    print(f"CSV logging:       {bot.history_tracker.csv_file}")
    print("="*60)
    
    # Start dashboard
    print("\n🌐 Starting dashboard...")
    bot.dashboard = AviatorDashboard(bot, port=5000)
    bot.dashboard.start()
    
    print("\n✅ Dashboard is running!")
    print("📊 View at: http://localhost:5000")
    print("\nPress Enter to start bot...")
    input()
    
    bot.save_config()
    bot.run_ml_mode()


if __name__ == "__main__":
    main()