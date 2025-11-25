"""
Multiplier API Routes
Provides REST endpoints for logging multiplier values to the database
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Create blueprint
multiplier_bp = Blueprint('multiplier', __name__, url_prefix='/api/multiplier')


def init_multiplier_api(app, multiplier_logger):
    """
    Initialize multiplier API routes with the Flask app.

    Args:
        app: Flask application instance
        multiplier_logger: MultiplierLogger instance
    """

    @multiplier_bp.route('/log', methods=['POST'])
    def log_multiplier():
        """
        Log a multiplier value to the database.

        Expected JSON body:
        {
            "bot_id": "bot_001",
            "multiplier": 1.23,
            "round_id": 123 (optional),
            "is_crash": false,
            "is_cashout": false,
            "ocr_confidence": 0.95,
            "game_name": "aviator",
            "platform_code": "demo"
        }

        Returns:
            JSON with status and record ID
        """
        try:
            data = request.get_json()

            if not data or 'bot_id' not in data or 'multiplier' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields: bot_id, multiplier'
                }), 400

            # Extract data
            bot_id = data.get('bot_id')
            multiplier = float(data.get('multiplier', 1.0))
            round_id = data.get('round_id')
            is_crash = data.get('is_crash', False)
            is_cashout = data.get('is_cashout', False)
            ocr_confidence = data.get('ocr_confidence')
            game_name = data.get('game_name', 'aviator')
            platform_code = data.get('platform_code', 'demo')
            timestamp_str = data.get('timestamp')

            # Parse timestamp if provided
            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except:
                    pass

            # Log the multiplier
            record_id = multiplier_logger.log_multiplier(
                bot_id=bot_id,
                round_id=round_id,
                multiplier=multiplier,
                timestamp=timestamp,
                is_crash=is_crash,
                is_cashout=is_cashout,
                ocr_confidence=ocr_confidence,
                game_name=game_name,
                platform_code=platform_code
            )

            if record_id:
                return jsonify({
                    'status': 'success',
                    'message': f'Multiplier {multiplier}x logged successfully',
                    'record_id': record_id,
                    'timestamp': (timestamp or datetime.utcnow()).isoformat()
                }), 201
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to log multiplier'
                }), 500

        except Exception as e:
            logger.error(f"❌ Error in log_multiplier endpoint: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @multiplier_bp.route('/create_round', methods=['POST'])
    def create_round():
        """
        Create a new crash game round.

        Expected JSON body:
        {
            "bot_id": "bot_001",
            "round_number": 1,
            "stake_value": 25.0,
            "strategy_name": "custom",
            "game_name": "aviator",
            "platform_code": "demo",
            "session_id": "session_123"
        }

        Returns:
            JSON with status and round ID
        """
        try:
            data = request.get_json()

            if not data or 'bot_id' not in data or 'round_number' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields: bot_id, round_number'
                }), 400

            # Extract data
            bot_id = data.get('bot_id')
            round_number = int(data.get('round_number'))
            stake_value = float(data.get('stake_value', 0.0))
            strategy_name = data.get('strategy_name', 'custom')
            game_name = data.get('game_name', 'aviator')
            platform_code = data.get('platform_code', 'demo')
            session_id = data.get('session_id', 'demo_session')

            # Create round
            round_id = multiplier_logger.create_round(
                bot_id=bot_id,
                round_number=round_number,
                stake_value=stake_value,
                strategy_name=strategy_name,
                game_name=game_name,
                platform_code=platform_code,
                session_id=session_id
            )

            if round_id:
                return jsonify({
                    'status': 'success',
                    'message': f'Round {round_number} created successfully',
                    'round_id': round_id
                }), 201
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to create round'
                }), 500

        except Exception as e:
            logger.error(f"❌ Error in create_round endpoint: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @multiplier_bp.route('/latest_round/<bot_id>', methods=['GET'])
    def get_latest_round(bot_id: str):
        """
        Get the latest active round for a bot.

        Args:
            bot_id: Bot identifier (in URL)

        Returns:
            JSON with round data or None
        """
        try:
            round_data = multiplier_logger.get_latest_round(bot_id)

            if round_data:
                return jsonify({
                    'status': 'success',
                    'round': round_data
                }), 200
            else:
                return jsonify({
                    'status': 'success',
                    'message': 'No active round found',
                    'round': None
                }), 200

        except Exception as e:
            logger.error(f"❌ Error in get_latest_round endpoint: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # Register blueprint
    app.register_blueprint(multiplier_bp)
    logger.info("✅ Multiplier API routes registered")
