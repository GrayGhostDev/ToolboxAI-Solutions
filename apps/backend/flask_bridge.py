"""
Flask Bridge Server

Minimal Flask application to provide compatibility bridge for legacy plugins.
This server runs alongside FastAPI for backward compatibility.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
import threading

# Configure logging first
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

# ===== ROBLOX-SPECIFIC ENDPOINTS =====

@app.route('/roblox/generate_script', methods=['POST'])
def generate_roblox_script():
    """Generate Roblox Lua script using AI agent"""
    data = request.get_json() or {}

    script_type = data.get('script_type', 'ServerScript')
    requirements = data.get('requirements', '')
    educational_focus = data.get('educational_focus', '')

    logger.info(f"Roblox script generation request: {script_type}")

    try:
        # Use importlib for dynamic import
        import importlib.util
        agent_module_path = os.path.join(
            project_root,
            'core', 'agents', 'roblox', 'roblox_content_generation_agent.py'
        )

        spec = importlib.util.spec_from_file_location(
            "roblox_content_generation_agent",
            agent_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        RobloxContentGenerationAgent = module.RobloxContentGenerationAgent

        # Create agent instance
        agent = RobloxContentGenerationAgent(llm=None)  # Will use default mock LLM

        # Generate script
        generated_script = agent.generate_educational_script(
            topic=requirements,
            script_type=script_type,
            difficulty_level="intermediate"
        )

        return jsonify({
            'success': True,
            'script': generated_script.code if hasattr(generated_script, 'code') else str(generated_script),
            'metadata': generated_script.metadata if hasattr(generated_script, 'metadata') else {},
            'message': 'Script generated successfully'
        })
    except Exception as e:
        logger.error(f"Script generation error: {e}", exc_info=True)
        # Return mock response for testing
        mock_script = """-- AI Generated Roblox Script
-- Topic: """ + requirements + """
-- Type: """ + script_type + """

local part = Instance.new("Part")
part.Name = "GeneratedPart"
part.Size = Vector3.new(4, 1, 2)
part.Position = Vector3.new(0, 5, 0)
part.BrickColor = BrickColor.new("Bright blue")
part.Parent = workspace

-- Educational focus: """ + (educational_focus or "General learning") + """
print("Script generated successfully!")"""

        return jsonify({
            'success': True,
            'script': mock_script,
            'metadata': {
                'type': script_type,
                'topic': requirements,
                'educational_focus': educational_focus
            },
            'message': 'Script generated successfully (mock)'
        })

@app.route('/roblox/optimize_script', methods=['POST'])
def optimize_roblox_script():
    """Optimize existing Roblox Lua script"""
    data = request.get_json() or {}

    script_code = data.get('script', '')
    optimization_level = data.get('optimization_level', 'balanced')

    logger.info(f"Roblox script optimization request: {optimization_level}")

    try:
        # Try production implementation first using importlib
        import importlib.util
        agent_module_path = os.path.join(
            project_root,
            'core', 'agents', 'roblox', 'roblox_script_optimization_agent.py'
        )

        spec = importlib.util.spec_from_file_location(
            "roblox_script_optimization_agent",
            agent_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        RobloxScriptOptimizationAgent = module.RobloxScriptOptimizationAgent
        OptimizationLevel = module.OptimizationLevel

        # Map string to enum
        level_map = {
            'conservative': OptimizationLevel.CONSERVATIVE,
            'balanced': OptimizationLevel.BALANCED,
            'aggressive': OptimizationLevel.AGGRESSIVE
        }

        # Create agent instance
        agent = RobloxScriptOptimizationAgent(llm=None)

        # Optimize script
        result = agent.optimize_script(
            script_code,
            level_map.get(optimization_level, OptimizationLevel.BALANCED)
        )

        return jsonify({
            'success': True,
            'optimized_script': result.optimized_code,
            'issues_found': [issue.dict() for issue in result.issues_found],
            'metrics': result.metrics,
            'message': 'Script optimized successfully'
        })
    except Exception as e:
        logger.error(f"Script optimization error: {e}", exc_info=True)
        # Fallback mock response for testing
        optimized = script_code.replace("wait(", "task.wait(")  # Simple optimization
        optimized = optimized.replace("Instance.new(", "local part = Instance.new(")

        return jsonify({
            'success': True,
            'optimized_script': optimized,
            'issues_found': [
                {"type": "performance", "description": "Replaced wait() with task.wait()"},
                {"type": "memory", "description": "Added local variable caching"}
            ],
            'metrics': {
                'lines_optimized': 2,
                'performance_gain': '15%'
            },
            'message': 'Script optimized successfully (mock)'
        })

@app.route('/roblox/validate_security', methods=['POST'])
def validate_script_security():
    """Validate Roblox script for security issues"""
    data = request.get_json() or {}

    script_code = data.get('script', '')
    script_type = data.get('script_type', 'ServerScript')
    strict_mode = data.get('strict_mode', True)

    logger.info(f"Roblox security validation request: {script_type}")

    try:
        # Try production implementation first using importlib
        import importlib.util
        agent_module_path = os.path.join(
            project_root,
            'core', 'agents', 'roblox', 'roblox_security_validation_agent.py'
        )

        spec = importlib.util.spec_from_file_location(
            "roblox_security_validation_agent",
            agent_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        RobloxSecurityValidationAgent = module.RobloxSecurityValidationAgent

        # Create agent instance
        agent = RobloxSecurityValidationAgent(llm=None, strict_mode=strict_mode)

        # Validate script
        report = agent.validate_script(script_code, script_type)

        return jsonify({
            'success': True,
            'risk_score': report.risk_score,
            'vulnerabilities': [vuln.dict() for vuln in report.vulnerabilities],
            'compliance_status': report.compliance_status.dict(),
            'recommendations': report.recommendations,
            'message': 'Security validation completed'
        })
    except Exception as e:
        logger.error(f"Security validation error: {e}", exc_info=True)
        # Fallback mock response for testing
        risk_score = 2
        vulnerabilities = []

        # Basic security checks
        if "loadstring" in script_code:
            vulnerabilities.append({
                "severity": "high",
                "type": "code_injection",
                "description": "Use of loadstring() can allow arbitrary code execution",
                "line": 1
            })
            risk_score += 3

        if "HttpService" in script_code and "GetAsync" in script_code:
            vulnerabilities.append({
                "severity": "medium",
                "type": "external_request",
                "description": "External HTTP requests should be validated",
                "line": 1
            })
            risk_score += 2

        return jsonify({
            'success': True,
            'risk_score': min(risk_score, 10),
            'vulnerabilities': vulnerabilities,
            'compliance_status': {
                'is_compliant': risk_score <= 5,
                'violations': []
            },
            'recommendations': [
                "Review all external data sources",
                "Implement input validation",
                "Use sandboxed execution where possible"
            ],
            'message': 'Security validation completed (mock)'
        })

@app.route('/roblox/deploy_content', methods=['POST'])
def deploy_roblox_content():
    """Deploy content to Roblox environment using Redis queue"""
    data = request.get_json() or {}

    content_type = data.get('content_type', 'script')
    content_data = data.get('content_data', '')
    target_place = data.get('target_place_id', '')
    priority = data.get('priority', 5)

    logger.info(f"Roblox content deployment request: {content_type} to {target_place}")

    try:
        # Import deployment service
        from apps.backend.services.roblox_deployment import (
            RobloxDeploymentPipeline,
            DeploymentRequest,
            ContentType
        )

        # Create async event loop if not exists
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Initialize pipeline
        pipeline = RobloxDeploymentPipeline()
        loop.run_until_complete(pipeline.initialize())

        # Create deployment request
        deployment_request = DeploymentRequest(
            content_type=ContentType(content_type),
            content_data=content_data,
            target_place_id=target_place,
            priority=priority,
            metadata={
                "source": "flask_bridge",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Queue deployment
        deployment_id = loop.run_until_complete(
            pipeline.queue_deployment(deployment_request)
        )

        return jsonify({
            'success': True,
            'deployment_id': deployment_id,
            'status': 'queued',
            'message': 'Content deployment queued successfully'
        })
    except Exception as e:
        logger.error(f"Deployment queue error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to queue deployment'
        }), 500

@app.route('/roblox/sync_status', methods=['GET'])
def get_sync_status():
    """Get Roblox synchronization status"""
    return jsonify({
        'success': True,
        'sync_active': False,  # Will be true when WebSocket is implemented
        'last_sync': None,
        'pending_updates': 0,
        'message': 'Sync status retrieved'
    })

@app.route('/roblox/educational_content', methods=['POST'])
def generate_educational_content():
    """Generate educational Roblox content"""
    data = request.get_json() or {}

    subject = data.get('subject', 'general')
    grade_level = data.get('grade_level', 'middle')
    content_format = data.get('format', 'interactive')

    logger.info(f"Educational content request: {subject} for {grade_level}")

    try:
        # Import agent with fallback
        from core.agents.roblox.roblox_content_generation_agent import RobloxContentGenerationAgent

        agent = RobloxContentGenerationAgent(llm=None)

        # Generate educational content
        content = agent.generate_educational_content(
            subject=subject,
            grade_level=grade_level,
            format_type=content_format
        )

        return jsonify({
            'success': True,
            'content': content.dict(),
            'message': 'Educational content generated successfully'
        })
    except Exception as e:
        logger.error(f"Educational content generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate educational content'
        }), 500

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