"""
JWT Security Manager

Integrates secure JWT secret generation and management with the
ToolboxAI authentication system, providing automatic secret validation,
rotation capabilities, and enhanced security features.
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from .jwt_secret_generator import JWTSecretGenerator
from ..secrets import get_secret, get_required_secret, SecretsManager

logger = logging.getLogger(__name__)

class JWTSecurityManager:
    """Enhanced JWT security manager with automatic secret validation and rotation"""
    
    def __init__(self, secrets_manager: Optional[SecretsManager] = None):
        self.secrets_manager = secrets_manager
        self.generator = JWTSecretGenerator()
        self._current_secret: Optional[str] = None
        self._secret_validated = False
        
    def initialize(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Initialize JWT security with validation and auto-generation
        
        Returns:
            Tuple of (success, status_report)
        """
        status_report = {
            'secret_source': 'unknown',
            'validation_passed': False,
            'auto_generated': False,
            'warnings': [],
            'actions_taken': []
        }
        
        try:
            # Try to get existing secret
            existing_secret = self._get_existing_secret()
            
            if existing_secret:
                # Validate existing secret
                is_valid, validation_report = self.generator.validate_secret(existing_secret)
                status_report['validation_passed'] = is_valid
                
                if is_valid:
                    self._current_secret = existing_secret
                    self._secret_validated = True
                    status_report['secret_source'] = 'environment_valid'
                    status_report['actions_taken'].append('Using existing valid secret')
                    logger.info("JWT secret validation passed")
                    
                else:
                    # Invalid secret - generate new one
                    status_report['warnings'].extend(validation_report['issues'])
                    new_secret = self._generate_and_replace_secret()
                    
                    if new_secret:
                        self._current_secret = new_secret
                        self._secret_validated = True
                        status_report['auto_generated'] = True
                        status_report['secret_source'] = 'auto_generated'
                        status_report['actions_taken'].append('Generated new secure secret')
                        status_report['warnings'].append('Old weak secret replaced')
                        logger.warning("Weak JWT secret detected and replaced with secure version")
                    else:
                        status_report['warnings'].append('Failed to generate replacement secret')
                        logger.error("Failed to replace weak JWT secret")
                        return False, status_report
                        
            else:
                # No secret found - generate one
                new_secret = self._generate_and_replace_secret()
                
                if new_secret:
                    self._current_secret = new_secret
                    self._secret_validated = True
                    status_report['auto_generated'] = True
                    status_report['secret_source'] = 'auto_generated'
                    status_report['actions_taken'].append('Generated initial secure secret')
                    logger.info("No JWT secret found, generated secure secret")
                else:
                    status_report['warnings'].append('Failed to generate initial secret')
                    logger.error("Failed to generate initial JWT secret")
                    return False, status_report
            
            return True, status_report
            
        except Exception as e:
            logger.error(f"JWT security initialization failed: {e}")
            status_report['warnings'].append(f'Initialization error: {str(e)}')
            return False, status_report
    
    def _get_existing_secret(self) -> Optional[str]:
        """Get existing JWT secret from environment or secrets manager"""
        # Try secrets manager first
        if self.secrets_manager:
            secret = self.secrets_manager.get('JWT_SECRET_KEY')
            if secret:
                return secret
        
        # Fallback to environment variable
        return os.getenv('JWT_SECRET_KEY')
    
    def _generate_and_replace_secret(self) -> Optional[str]:
        """Generate new secure secret and provide instructions for deployment"""
        try:
            # Generate secure secret
            new_secret, secret_id = self.generator.generate_and_store_secret(
                "Auto-generated secure JWT secret"
            )
            
            # Create deployment instructions
            instructions = self.generator.create_environment_instructions(new_secret, secret_id)
            
            # Save instructions to file for deployment
            instructions_file = Path('.secrets/jwt_deployment_instructions.txt')
            instructions_file.parent.mkdir(exist_ok=True)
            
            with open(instructions_file, 'w') as f:
                f.write(instructions)
            
            os.chmod(instructions_file, 0o600)
            
            # Log instructions path
            logger.warning(f"New JWT secret generated. Deployment instructions saved to: {instructions_file}")
            logger.warning("IMPORTANT: Update your environment variables with the new secret!")
            
            return new_secret
            
        except Exception as e:
            logger.error(f"Failed to generate JWT secret: {e}")
            return None
    
    def get_validated_secret(self) -> str:
        """
        Get the validated JWT secret
        
        Returns:
            Validated JWT secret
            
        Raises:
            ValueError: If no valid secret is available
        """
        if not self._secret_validated or not self._current_secret:
            success, status = self.initialize()
            if not success:
                raise ValueError(f"No valid JWT secret available: {status.get('warnings', [])}")
        
        return self._current_secret
    
    def validate_current_secret(self) -> Dict[str, Any]:
        """
        Validate the currently configured JWT secret
        
        Returns:
            Validation report
        """
        secret = self._get_existing_secret()
        
        if not secret:
            return {
                'valid': False,
                'issues': ['No JWT secret configured'],
                'recommendations': ['Generate and configure a secure JWT secret']
            }
        
        is_valid, report = self.generator.validate_secret(secret)
        report['valid'] = is_valid
        
        return report
    
    def _validate_environment_jwt_secret(self) -> None:
        """
        Validate JWT secret for production environment
        
        Raises:
            ValueError: If JWT secret is weak in production environment
        """
        environment = os.getenv('ENV_NAME', os.getenv('ENVIRONMENT', 'development'))
        
        # Only validate in production
        if environment.lower() == 'production':
            secret = self._get_existing_secret()
            
            if not secret:
                raise ValueError("PRODUCTION SECURITY ERROR: No JWT secret configured")
            
            # Check minimum length
            if len(secret) < 32:
                raise ValueError("PRODUCTION SECURITY ERROR: JWT secret too short (min 32 chars)")
            
            # Check for common weak patterns
            weak_patterns = ['weak', 'test', 'demo', 'example', 'password', '123', 'abc']
            if any(pattern in secret.lower() for pattern in weak_patterns):
                raise ValueError("PRODUCTION SECURITY ERROR: JWT secret contains weak patterns")
            
            # Check entropy (character diversity)
            unique_chars = len(set(secret))
            if unique_chars < 16:
                raise ValueError("PRODUCTION SECURITY ERROR: JWT secret has low entropy")
            
            # Use the generator's validation for comprehensive check
            is_valid, report = self.generator.validate_secret(secret)
            if not is_valid:
                issues = report.get('issues', ['Unknown validation failure'])
                raise ValueError(f"PRODUCTION SECURITY ERROR: {'; '.join(issues)}")
    
    def rotate_secret(self, force: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Rotate JWT secret
        
        Args:
            force: Force rotation even if current secret is valid
            
        Returns:
            Tuple of (success, rotation_report)
        """
        rotation_report = {
            'success': False,
            'old_secret_id': None,
            'new_secret_id': None,
            'rotation_reason': '',
            'instructions_file': None
        }
        
        try:
            # Get current secret info
            current_secret = self._get_existing_secret()
            
            if not force and current_secret:
                # Check if rotation is needed
                is_valid, validation = self.generator.validate_secret(current_secret)
                if is_valid:
                    rotation_report['rotation_reason'] = 'Rotation not needed - current secret is valid'
                    return False, rotation_report
            
            # Perform rotation
            old_secret_id = getattr(self, '_current_secret_id', None)
            new_secret, new_secret_id = self.generator.rotate_secret(old_secret_id)
            
            # Update current secret
            self._current_secret = new_secret
            self._secret_validated = True
            
            # Generate deployment instructions
            instructions = self.generator.create_environment_instructions(new_secret, new_secret_id)
            instructions_file = Path(f'.secrets/jwt_rotation_{new_secret_id}_instructions.txt')
            
            with open(instructions_file, 'w') as f:
                f.write(instructions)
            
            os.chmod(instructions_file, 0o600)
            
            rotation_report.update({
                'success': True,
                'old_secret_id': old_secret_id,
                'new_secret_id': new_secret_id,
                'rotation_reason': 'Manual rotation' if force else 'Weak secret replacement',
                'instructions_file': str(instructions_file)
            })
            
            logger.info(f"JWT secret rotated successfully: {new_secret_id}")
            logger.warning(f"Update environment variables using instructions in: {instructions_file}")
            
            return True, rotation_report
            
        except Exception as e:
            logger.error(f"JWT secret rotation failed: {e}")
            rotation_report['rotation_reason'] = f'Rotation failed: {str(e)}'
            return False, rotation_report
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get comprehensive JWT security status
        
        Returns:
            Security status report
        """
        status = {
            'secret_configured': False,
            'secret_valid': False,
            'validation_details': {},
            'security_level': 'unknown',
            'recommendations': [],
            'last_validation': None
        }
        
        try:
            # Check if secret is configured
            secret = self._get_existing_secret()
            status['secret_configured'] = bool(secret)
            
            if secret:
                # Validate secret
                is_valid, validation_report = self.generator.validate_secret(secret)
                status['secret_valid'] = is_valid
                status['validation_details'] = validation_report
                status['last_validation'] = datetime.utcnow().isoformat()
                
                # Determine security level
                if is_valid:
                    if validation_report['entropy_score'] > 4.0 and len(secret) >= 64:
                        status['security_level'] = 'high'
                    elif validation_report['entropy_score'] > 3.0 and len(secret) >= 32:
                        status['security_level'] = 'medium'
                    else:
                        status['security_level'] = 'low'
                        status['recommendations'].append('Consider using a longer, more complex secret')
                else:
                    status['security_level'] = 'vulnerable'
                    status['recommendations'].extend(validation_report['recommendations'])
                    
            else:
                status['security_level'] = 'critical'
                status['recommendations'].append('Configure a JWT secret immediately')
                
        except Exception as e:
            logger.error(f"Error checking JWT security status: {e}")
            status['security_level'] = 'error'
            status['recommendations'].append(f'Fix security status check error: {str(e)}')
        
        return status


# Global JWT security manager instance
_jwt_security_manager: Optional[JWTSecurityManager] = None

def init_jwt_security(secrets_manager: Optional[SecretsManager] = None) -> JWTSecurityManager:
    """
    Initialize global JWT security manager
    
    Args:
        secrets_manager: Optional secrets manager instance
        
    Returns:
        JWT security manager instance
    """
    global _jwt_security_manager
    _jwt_security_manager = JWTSecurityManager(secrets_manager)
    
    # Initialize security
    success, status = _jwt_security_manager.initialize()
    
    if not success:
        logger.error(f"JWT security initialization failed: {status}")
    else:
        logger.info("JWT security initialized successfully")
        
    return _jwt_security_manager

def get_jwt_security_manager() -> Optional[JWTSecurityManager]:
    """Get the global JWT security manager instance"""
    return _jwt_security_manager

def get_secure_jwt_secret() -> str:
    """
    Get the secure JWT secret for use in authentication
    
    Returns:
        Validated JWT secret
        
    Raises:
        ValueError: If no valid secret is available
    """
    if not _jwt_security_manager:
        # Initialize if not already done
        init_jwt_security()
    
    if _jwt_security_manager:
        return _jwt_security_manager.get_validated_secret()
    
    raise ValueError("JWT security manager not available")

# For backward compatibility
def ensure_secure_jwt_secret() -> str:
    """Ensure a secure JWT secret is available and return it"""
    return get_secure_jwt_secret()
