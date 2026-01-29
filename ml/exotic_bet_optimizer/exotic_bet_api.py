"""
Exotic Bet Optimizer API Routes
===============================

Flask/FastAPI integration for the Exotic Bet Optimizer
Provides REST endpoints for the equine-oracle-backend
"""

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime
import traceback

from exotic_bet_optimizer import (
    ExoticBetOptimizer, 
    Horse, 
    ExoticBet, 
    ProbabilityCalibrator,
    ExoticCombinationGenerator,
    EVSignalGenerator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for exotic betting routes
exotic_bp = Blueprint('exotic_bets', __name__, url_prefix='/api/v1/exotic')

# Global optimizer instance
optimizer = ExoticBetOptimizer()


@exotic_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Exotic Bet Optimizer',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@exotic_bp.route('/optimize', methods=['POST'])
def optimize_exotic_bets():
    """
    Main optimization endpoint
    
    Expected JSON payload:
    {
        "race_id": "string",
        "horses": [
            {
                "id": int,
                "name": "string",
                "win_probability": float,
                "odds": float,
                "jockey": "string",
                "trainer": "string",
                "form_rating": float,
                "speed_rating": float,
                "class_rating": float
            }
        ],
        "options": {
            "max_exacta": int (default: 20),
            "max_trifecta": int (default: 15),
            "max_superfecta": int (default: 10),
            "min_ev_threshold": float (default: 0.05)
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'horses' not in data:
            return jsonify({
                'error': 'Missing required field: horses',
                'status': 'error'
            }), 400
        
        # Parse horses from request
        horses = []
        for horse_data in data['horses']:
            try:
                horse = Horse(
                    id=horse_data['id'],
                    name=horse_data['name'],
                    win_probability=horse_data.get('win_probability', 0.1),
                    place_probability=horse_data.get('place_probability', 0.2),
                    show_probability=horse_data.get('show_probability', 0.3),
                    odds=horse_data['odds'],
                    jockey=horse_data.get('jockey', 'Unknown'),
                    trainer=horse_data.get('trainer', 'Unknown'),
                    form_rating=horse_data.get('form_rating', 75.0),
                    speed_rating=horse_data.get('speed_rating', 80.0),
                    class_rating=horse_data.get('class_rating', 75.0)
                )
                horses.append(horse)
            except KeyError as e:
                return jsonify({
                    'error': f'Missing required horse field: {str(e)}',
                    'status': 'error'
                }), 400
        
        # Parse options
        options = data.get('options', {})
        
        # Update optimizer settings if provided
        if 'min_ev_threshold' in options:
            optimizer.signal_generator.min_ev_threshold = options['min_ev_threshold']
        
        # Run optimization
        results = optimizer.optimize_exotic_bets(horses)
        
        # Add race metadata
        results['race_id'] = data.get('race_id', 'unknown')
        results['request_timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Optimization completed for race {data.get('race_id', 'unknown')} with {len(horses)} horses")
        
        return jsonify({
            'status': 'success',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error in optimize_exotic_bets: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'status': 'error'
        }), 500


@exotic_bp.route('/probabilities/calibrate', methods=['POST'])
def calibrate_probabilities():
    """
    Endpoint to calibrate horse probabilities only
    
    Expected JSON payload:
    {
        "horses": [horse_objects]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'horses' not in data:
            return jsonify({'error': 'Missing required field: horses'}), 400
        
        horses = []
        for horse_data in data['horses']:
            horse = Horse(
                id=horse_data['id'],
                name=horse_data['name'],
                win_probability=horse_data.get('win_probability', 0.1),
                place_probability=horse_data.get('place_probability', 0.2),
                show_probability=horse_data.get('show_probability', 0.3),
                odds=horse_data['odds'],
                jockey=horse_data.get('jockey', 'Unknown'),
                trainer=horse_data.get('trainer', 'Unknown'),
                form_rating=horse_data.get('form_rating', 75.0),
                speed_rating=horse_data.get('speed_rating', 80.0),
                class_rating=horse_data.get('class_rating', 75.0)
            )
            horses.append(horse)
        
        calibrated_horses = optimizer.calibrator.calibrate_win_probabilities(horses)
        
        # Format response
        response = {
            'status': 'success',
            'calibrated_horses': [
                {
                    'id': h.id,
                    'name': h.name,
                    'original_win_probability': next(orig.win_probability for orig in horses if orig.id == h.id),
                    'calibrated_win_probability': h.win_probability,
                    'calibrated_place_probability': h.place_probability,
                    'calibrated_show_probability': h.show_probability
                }
                for h in calibrated_horses
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in calibrate_probabilities: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@exotic_bp.route('/combinations/<bet_type>', methods=['POST'])
def generate_combinations(bet_type):
    """
    Generate combinations for specific bet type
    
    Supported bet_types: exacta, trifecta, superfecta
    """
    try:
        if bet_type not in ['exacta', 'trifecta', 'superfecta']:
            return jsonify({'error': 'Invalid bet type. Supported: exacta, trifecta, superfecta'}), 400
        
        data = request.get_json()
        
        if not data or 'horses' not in data:
            return jsonify({'error': 'Missing required field: horses'}), 400
        
        horses = []
        for horse_data in data['horses']:
            horse = Horse(
                id=horse_data['id'],
                name=horse_data['name'],
                win_probability=horse_data.get('win_probability', 0.1),
                place_probability=horse_data.get('place_probability', 0.2),
                show_probability=horse_data.get('show_probability', 0.3),
                odds=horse_data['odds'],
                jockey=horse_data.get('jockey', 'Unknown'),
                trainer=horse_data.get('trainer', 'Unknown'),
                form_rating=horse_data.get('form_rating', 75.0),
                speed_rating=horse_data.get('speed_rating', 80.0),
                class_rating=horse_data.get('class_rating', 75.0)
            )
            horses.append(horse)
        
        # Calibrate probabilities first
        calibrated_horses = optimizer.calibrator.calibrate_win_probabilities(horses)
        
        # Generate combinations based on bet type
        max_combinations = data.get('max_combinations', 20)
        
        if bet_type == 'exacta':
            combinations = optimizer.combination_generator.generate_exacta_combinations(
                calibrated_horses, max_combinations
            )
        elif bet_type == 'trifecta':
            combinations = optimizer.combination_generator.generate_trifecta_combinations(
                calibrated_horses, max_combinations
            )
        elif bet_type == 'superfecta':
            combinations = optimizer.combination_generator.generate_superfecta_combinations(
                calibrated_horses, max_combinations
            )
        
        # Format response
        response = {
            'status': 'success',
            'bet_type': bet_type,
            'total_combinations': len(combinations),
            'combinations': [
                {
                    'combination': combo.combination,
                    'probability': combo.probability,
                    'expected_value': combo.expected_value,
                    'kelly_fraction': combo.kelly_fraction,
                    'confidence_score': combo.confidence_score,
                    'payout_odds': combo.payout_odds
                }
                for combo in combinations
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in generate_combinations: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@exotic_bp.route('/signals', methods=['POST'])
def generate_ev_signals():
    """
    Generate EV signals for profitable betting opportunities
    """
    try:
        data = request.get_json()
        
        if not data or 'horses' not in data:
            return jsonify({'error': 'Missing required field: horses'}), 400
        
        horses = []
        for horse_data in data['horses']:
            horse = Horse(
                id=horse_data['id'],
                name=horse_data['name'],
                win_probability=horse_data.get('win_probability', 0.1),
                place_probability=horse_data.get('place_probability', 0.2),
                show_probability=horse_data.get('show_probability', 0.3),
                odds=horse_data['odds'],
                jockey=horse_data.get('jockey', 'Unknown'),
                trainer=horse_data.get('trainer', 'Unknown'),
                form_rating=horse_data.get('form_rating', 75.0),
                speed_rating=horse_data.get('speed_rating', 80.0),
                class_rating=horse_data.get('class_rating', 75.0)
            )
            horses.append(horse)
        
        # Run full optimization to get all exotic bets
        calibrated_horses = optimizer.calibrator.calibrate_win_probabilities(horses)
        
        exacta_bets = optimizer.combination_generator.generate_exacta_combinations(calibrated_horses)
        trifecta_bets = optimizer.combination_generator.generate_trifecta_combinations(calibrated_horses)
        superfecta_bets = optimizer.combination_generator.generate_superfecta_combinations(calibrated_horses)
        
        all_exotic_bets = exacta_bets + trifecta_bets + superfecta_bets
        
        # Generate EV signals
        ev_signals = optimizer.signal_generator.generate_ev_signals(all_exotic_bets)
        
        response = {
            'status': 'success',
            'total_signals': len(ev_signals),
            'profitable_opportunities': len([s for s in ev_signals if s['expected_value'] > 0]),
            'signals': ev_signals,
            'summary': {
                'avg_expected_value': sum(s['expected_value'] for s in ev_signals) / len(ev_signals) if ev_signals else 0,
                'max_expected_value': max((s['expected_value'] for s in ev_signals), default=0),
                'total_recommended_stake': sum(s['recommended_stake'] for s in ev_signals)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in generate_ev_signals: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@exotic_bp.route('/analytics/performance', methods=['GET'])
def get_performance_analytics():
    """Get historical performance analytics"""
    try:
        # Get signal history for analytics
        top_signals = optimizer.signal_generator.get_top_signals(20)
        
        if not top_signals:
            return jsonify({
                'status': 'success',
                'message': 'No historical data available',
                'data': {
                    'total_signals': 0,
                    'performance_metrics': {}
                }
            })
        
        # Calculate performance metrics
        performance_metrics = {
            'total_historical_signals': len(top_signals),
            'avg_signal_strength': sum(s['signal_strength'] for s in top_signals) / len(top_signals),
            'avg_expected_value': sum(s['expected_value'] for s in top_signals) / len(top_signals),
            'risk_distribution': {
                'LOW': len([s for s in top_signals if s['risk_level'] == 'LOW']),
                'MEDIUM': len([s for s in top_signals if s['risk_level'] == 'MEDIUM']),
                'HIGH': len([s for s in top_signals if s['risk_level'] == 'HIGH']),
                'VERY_HIGH': len([s for s in top_signals if s['risk_level'] == 'VERY_HIGH'])
            },
            'bet_type_distribution': {
                'exacta': len([s for s in top_signals if s['bet_type'] == 'exacta']),
                'trifecta': len([s for s in top_signals if s['bet_type'] == 'trifecta']),
                'superfecta': len([s for s in top_signals if s['bet_type'] == 'superfecta'])
            }
        }
        
        response = {
            'status': 'success',
            'data': {
                'performance_metrics': performance_metrics,
                'top_signals': top_signals[:10],
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in get_performance_analytics: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


# Initialize Flask app for standalone testing
def create_app():
    """Create Flask app with CORS enabled"""
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprint
    app.register_blueprint(exotic_bp)
    
    @app.route('/')
    def index():
        return jsonify({
            'service': 'Exotic Bet Optimizer API',
            'version': '1.0.0',
            'endpoints': [
                '/api/v1/exotic/health',
                '/api/v1/exotic/optimize',
                '/api/v1/exotic/probabilities/calibrate',
                '/api/v1/exotic/combinations/<bet_type>',
                '/api/v1/exotic/signals',
                '/api/v1/exotic/analytics/performance'
            ]
        })
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)