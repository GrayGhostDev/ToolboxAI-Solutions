"""
Flask Bridge Server

Minimal Flask application to provide compatibility bridge for legacy plugins.
This server runs alongside FastAPI for backward compatibility.
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins="*")

# Configuration
app.config['PORT'] = int(os.getenv('FLASK_PORT', '5001'))
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Flask Bridge Server',
        'version': '1.0.0'
    })

@app.route('/register_plugin', methods=['POST'])
def register_plugin():
    """Legacy plugin registration endpoint"""
    data = request.get_json() or {}
    plugin_id = data.get('plugin_id', 'unknown')

    logger.info(f"Plugin registered: {plugin_id}")

    return jsonify({
        'success': True,
        'plugin_id': plugin_id,
        'message': 'Plugin registered successfully'
    })

@app.route('/plugin/<plugin_id>/heartbeat', methods=['POST'])
def plugin_heartbeat(plugin_id):
    """Plugin heartbeat endpoint"""
    logger.debug(f"Heartbeat received from plugin: {plugin_id}")

    return jsonify({
        'success': True,
        'plugin_id': plugin_id,
        'message': 'Heartbeat acknowledged'
    })

@app.route('/generate_content', methods=['POST'])
def generate_content():
    """Legacy content generation endpoint"""
    data = request.get_json() or {}
    content_type = data.get('type', 'unknown')

    logger.info(f"Content generation request: {content_type}")

    # Return mock response for compatibility
    return jsonify({
        'success': True,
        'content': {
            'type': content_type,
            'data': 'Mock content for compatibility'
        },
        'message': 'Content generated (mock)'
    })

@app.route('/status', methods=['GET'])
def get_status():
    """Server status endpoint"""
    return jsonify({
        'service': 'ToolboxAI Flask Bridge',
        'status': 'running',
        'uptime': 0,  # Could track actual uptime
        'connections': 0
    })

@app.route('/config', methods=['GET'])
def get_config():
    """Get server configuration"""
    return jsonify({
        'port': app.config['PORT'],
        'debug': app.config['DEBUG'],
        'cors_enabled': True
    })

@app.route('/config', methods=['POST'])
def update_config():
    """Update server configuration (mock)"""
    data = request.get_json() or {}
    logger.info(f"Config update request: {data}")

    return jsonify({
        'success': True,
        'message': 'Configuration updated (mock)'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

def run_server():
    """Run the Flask server"""
    port = app.config['PORT']
    debug = app.config['DEBUG']

    logger.info(f"Starting Flask bridge server on port {port}")

    try:
        app.run(
            host='127.0.0.1',
            port=port,
            debug=debug,
            use_reloader=False  # Disable reloader to avoid conflicts
        )
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        raise

if __name__ == '__main__':
    run_server()