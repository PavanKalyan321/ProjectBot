"""
Mobile Notifier - Send notifications to mobile devices
"""

import requests
import json
from datetime import datetime

class MobileNotifier:
    """Send notifications via multiple channels."""
    
    def __init__(self):
        self.telegram_token = None
        self.telegram_chat_id = None
        self.discord_webhook = None
        self.pushover_token = None
        self.pushover_user = None
        
    def setup_telegram(self, token, chat_id):
        """Setup Telegram notifications."""
        self.telegram_token = token
        self.telegram_chat_id = chat_id
        
    def setup_discord(self, webhook_url):
        """Setup Discord notifications."""
        self.discord_webhook = webhook_url
        
    def setup_pushover(self, token, user_key):
        """Setup Pushover notifications."""
        self.pushover_token = token
        self.pushover_user = user_key
    
    def send_telegram(self, message):
        """Send Telegram notification."""
        if not self.telegram_token or not self.telegram_chat_id:
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def send_discord(self, message):
        """Send Discord notification."""
        if not self.discord_webhook:
            return False
            
        try:
            data = {'content': message}
            response = requests.post(self.discord_webhook, json=data, timeout=10)
            return response.status_code == 204
        except:
            return False
    
    def send_pushover(self, message, title="Aviator Bot"):
        """Send Pushover notification."""
        if not self.pushover_token or not self.pushover_user:
            return False
            
        try:
            data = {
                'token': self.pushover_token,
                'user': self.pushover_user,
                'message': message,
                'title': title,
                'priority': 1
            }
            response = requests.post("https://api.pushover.net/1/messages.json", data=data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def notify_high_sequence_prediction(self, prediction_data):
        """Send notification for high sequence prediction."""
        confidence = prediction_data['confidence']
        reason = prediction_data['reason']
        
        message = f"""🚀 HIGH MULTIPLIER ALERT!
        
Confidence: {confidence}%
Pattern: {reason}
Time: {datetime.now().strftime('%H:%M:%S')}

🎯 Prepare for potential high multipliers!"""
        
        # Send to all configured channels
        self.send_telegram(message)
        self.send_discord(message)
        self.send_pushover(message, "High Multiplier Alert")
        
        return True
    
    def send_validation_result(self, result):
        """Send validation result notification."""
        if result['success']:
            status = "✅ PREDICTION SUCCESS"
            details = f"Started after: {result['start_delay']}min\nMax multiplier: {result['max_multiplier']:.1f}x"
            if result['duration']:
                details += f"\nDuration: {result['duration']}min"
        else:
            status = "❌ PREDICTION FAILED"
            details = "No high sequence detected in 30 minutes"
        
        message = f"""{status}
        
Prediction: {result['prediction_time']} ({result['confidence']}%)
{details}
        
📊 Validation complete"""
        
        self.send_telegram(message)
        self.send_discord(message)
        self.send_pushover(message, "Prediction Result")