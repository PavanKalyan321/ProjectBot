"""Web dashboard server for real-time bot monitoring."""

import os
import time
import threading
import webbrowser
from collections import deque
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO


class AviatorDashboard:
    """Real-time web dashboard for bot monitoring."""
    
    def __init__(self, bot, port=5000):
        """
        Initialize dashboard server.

        Args:
            bot: AviatorBotML instance
            port: Port number for web server
        """
        self.bot = bot
        self.port = port
        self.app = Flask(__name__, template_folder='templates')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.is_running = False
        self.round_history = deque(maxlen=100)
        self.highest_multipliers = []  # List to track top multipliers
        self.low_reds = deque(maxlen=20)  # Track recent low multipliers
        self.high_runs = deque(maxlen=50)  # Track high multiplier runs for graphing
        self._setup_routes()
        self._create_dashboard_template()
        
    def _setup_routes(self):
        """Setup Flask routes."""
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
                'cumulative_profit': profit,
                'highest_multipliers': self.highest_multipliers[:20],
                'low_reds': list(self.low_reds)
            })
    
    def emit_round_update(self, round_data):
        """
        Send round update to dashboard.
        
        Args:
            round_data: Dictionary containing round information
        """
        self.round_history.append(round_data)
        
        # Track highest multipliers
        multiplier = round_data.get('multiplier', 0)
        if multiplier > 0:
            self._update_highest_multipliers(multiplier, round_data.get('timestamp'))
            
            # Track low reds (multipliers < 2.0)
            if multiplier < 2.0:
                self.low_reds.append({
                    'multiplier': multiplier,
                    'timestamp': round_data.get('timestamp')
                })
        
        try:
            self.socketio.emit('round_update', round_data)
            # Emit updates for new sections
            self.socketio.emit('highest_multipliers_update', {
                'highest_multipliers': self.highest_multipliers[:20]
            })
            self.socketio.emit('low_reds_update', {
                'low_reds': list(self.low_reds)
            })
        except:
            pass
    
    def _update_highest_multipliers(self, multiplier, timestamp):
        """
        Update the highest multipliers list.
        
        Args:
            multiplier: Multiplier value
            timestamp: Timestamp of the round
        """
        entry = {'multiplier': multiplier, 'timestamp': timestamp}
        self.highest_multipliers.append(entry)
        # Sort by multiplier descending and keep top 20
        self.highest_multipliers.sort(key=lambda x: x['multiplier'], reverse=True)
        self.highest_multipliers = self.highest_multipliers[:20]
    
    def emit_stats_update(self):
        """Send stats update to dashboard."""
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
        """Create dashboard HTML file."""
        os.makedirs('templates', exist_ok=True)
        
        # Read the existing template
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.html')
        
        # If template doesn't exist in dashboard folder, create it
        if not os.path.exists(template_path):
            self._generate_dashboard_html(template_path)
    
    def _generate_dashboard_html(self, path):
        """Generate dashboard HTML content."""
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
        .stat-card:hover { transform: translateY(-2px); }
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
            grid-template-rows: 1fr 1fr;
            gap: 10px;
            overflow: hidden;
        }
        .panel.span-rows {
            grid-row: span 2;
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
        .rounds-table-container { flex: 1; overflow-y: auto; }
        .rounds-table { width: 100%; border-collapse: collapse; }
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
        .rounds-table tr:hover { background: rgba(255,255,255,0.1); }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
        }
        .badge.success { background: #10b981; color: #fff; }
        .badge.skip { background: #6b7280; color: #fff; }
        .badge.win { background: #22c55e; color: #fff; }
        .badge.loss { background: #dc2626; color: #fff; }
        .leaderboard-item {
            display: flex;
            align-items: center;
            padding: 8px 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin-bottom: 6px;
            transition: all 0.2s;
        }
        .leaderboard-item:hover {
            background: rgba(255,255,255,0.1);
            transform: translateX(4px);
        }
        .leaderboard-rank {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
            margin-right: 12px;
            flex-shrink: 0;
        }
        .leaderboard-rank.gold { background: linear-gradient(135deg, #fbbf24, #f59e0b); }
        .leaderboard-rank.silver { background: linear-gradient(135deg, #d1d5db, #9ca3af); }
        .leaderboard-rank.bronze { background: linear-gradient(135deg, #f97316, #ea580c); }
        .leaderboard-rank.default { background: rgba(255,255,255,0.2); }
        .leaderboard-mult {
            font-size: 18px;
            font-weight: bold;
            color: #10b981;
            margin-right: auto;
        }
        .leaderboard-time {
            font-size: 10px;
            opacity: 0.7;
        }
        .low-red-item {
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 20px;
            margin: 4px;
            font-size: 11px;
            transition: all 0.2s;
        }
        .low-red-item:hover {
            background: rgba(239, 68, 68, 0.3);
            transform: scale(1.05);
        }
        .low-red-mult {
            font-weight: bold;
            color: #ef4444;
            margin-right: 8px;
        }
        .low-red-time {
            opacity: 0.7;
            font-size: 10px;
        }
        .scrollable-content {
            flex: 1;
            overflow-y: auto;
            padding-right: 5px;
        }
        .low-reds-container {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: rgba(255,255,255,0.1); border-radius: 10px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.3); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.5); }
        @media (max-width: 1200px) {
            .main-content { 
                grid-template-columns: 1fr;
                grid-template-rows: auto;
            }
            .panel.span-rows {
                grid-row: span 1;
            }
            .stats-grid { grid-template-columns: repeat(3, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><div class="status-indicator"></div>✈️ Aviator Bot (Modular)</h1>
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
            <div class="panel span-rows">
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
                <h2>🏆 Highest Multipliers</h2>
                <div class="scrollable-content" id="highest-multipliers-container">
                    <div style="text-align: center; opacity: 0.5; padding: 20px; font-size: 12px;">
                        ⏳ Waiting for data...
                    </div>
                </div>
            </div>
            <div class="panel">
                <h2>🔴 Low Reds (< 2.0x)</h2>
                <div class="scrollable-content">
                    <div class="low-reds-container" id="low-reds-container">
                        <div style="text-align: center; opacity: 0.5; padding: 20px; font-size: 12px; width: 100%;">
                            ⏳ Waiting for data...
                        </div>
                    </div>
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
        });
        socket.on('stats_update', (data) => {
            updateStats(data.stats, data.current_stake);
        });
        socket.on('highest_multipliers_update', (data) => {
            updateHighestMultipliers(data.highest_multipliers);
        });
        socket.on('low_reds_update', (data) => {
            updateLowReds(data.low_reds);
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
        function updateHighestMultipliers(multipliers) {
            const container = document.getElementById('highest-multipliers-container');
            if (!multipliers || multipliers.length === 0) {
                container.innerHTML = '<div style="text-align: center; opacity: 0.5; padding: 20px; font-size: 12px;">No data yet</div>';
                return;
            }
            container.innerHTML = '';
            multipliers.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = 'leaderboard-item';
                
                const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : 'default';
                const time = new Date(item.timestamp).toLocaleTimeString('en-US', {
                    hour12: false, hour: '2-digit', minute: '2-digit'
                });
                
                div.innerHTML = `
                    <div class="leaderboard-rank ${rankClass}">${index + 1}</div>
                    <div class="leaderboard-mult">${item.multiplier.toFixed(2)}x</div>
                    <div class="leaderboard-time">${time}</div>
                `;
                container.appendChild(div);
            });
        }
        function updateLowReds(lowReds) {
            const container = document.getElementById('low-reds-container');
            if (!lowReds || lowReds.length === 0) {
                container.innerHTML = '<div style="text-align: center; opacity: 0.5; padding: 20px; font-size: 12px; width: 100%;">No low reds yet</div>';
                return;
            }
            container.innerHTML = '';
            // Show most recent first
            [...lowReds].reverse().forEach(item => {
                const div = document.createElement('div');
                div.className = 'low-red-item';
                
                const time = new Date(item.timestamp).toLocaleTimeString('en-US', {
                    hour12: false, hour: '2-digit', minute: '2-digit'
                });
                
                div.innerHTML = `
                    <span class="low-red-mult">${item.multiplier.toFixed(2)}x</span>
                    <span class="low-red-time">${time}</span>
                `;
                container.appendChild(div);
            });
        }
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                updateStats(data.stats, data.current_stake);
                data.history.forEach(round => {
                    addRoundToTable(round);
                });
                if (data.highest_multipliers) {
                    updateHighestMultipliers(data.highest_multipliers);
                }
                if (data.low_reds) {
                    updateLowReds(data.low_reds);
                }
            });
    </script>
</body>
</html>'''
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def start(self):
        """Start dashboard server in background thread."""
        if self.is_running:
            return
        
        self.is_running = True
        thread = threading.Thread(
            target=lambda: self.socketio.run(
                self.app, 
                port=self.port, 
                debug=False, 
                use_reloader=False, 
                log_output=False
            ),
            daemon=True
        )
        thread.start()
        time.sleep(1.5)
        
        try:
            webbrowser.open(f'http://localhost:{self.port}')
        except:
            pass
        
        print(f"✓ Dashboard running at http://localhost:{self.port}")
