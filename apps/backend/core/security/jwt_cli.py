#!/usr/bin/env python3
"""
JWT Security CLI Tool

Command-line interface for managing JWT secrets and testing security configuration
for the ToolboxAI authentication system.
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def generate_secret(args):
    """Generate a new JWT secret"""
    try:
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        
        if args.hex:
            secret = generator.generate_hex_secret(args.length)
        elif args.base64:
            secret = generator.generate_base64_secret(args.length // 2)
        else:
            secret = generator.generate_secure_secret(args.length)
        
        if args.store:
            secret_id = generator.store_secret_securely(secret, "CLI generated secret")
            print(f"Secret generated and stored with ID: {secret_id}")
            
        if args.instructions:
            instructions = generator.create_environment_instructions(secret, getattr(args, 'secret_id', 'cli-generated'))
            print("\n" + instructions)
        else:
            print(f"Generated JWT secret: {secret}")
            print(f"Length: {len(secret)} characters")
            
    except ImportError as e:
        print(f"Error: JWT security module not available: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating secret: {e}")
        sys.exit(1)

def validate_secret(args):
    """Validate a JWT secret"""
    try:
        from apps.backend.core.security.jwt import JWTSecretGenerator
        
        generator = JWTSecretGenerator()
        secret = args.secret
        
        if not secret:
            # Try to get from environment
            secret = os.getenv('JWT_SECRET_KEY')
            if not secret:
                print("Error: No secret provided. Use --secret or set JWT_SECRET_KEY environment variable")
                sys.exit(1)
        
        is_valid, report = generator.validate_secret(secret)
        
        print(f"Secret validation: {'✓ VALID' if is_valid else '✗ INVALID'}")
        print(f"Length: {len(secret)} characters")
        print(f"Entropy: {report['entropy_score']:.2f} bits/character")
        print(f"Character diversity: {report['character_diversity']} unique characters")
        
        if report['issues']:
            print("\n⚠️  Issues found:")
            for issue in report['issues']:
                print(f"  • {issue}")
                
        if report['recommendations']:
            print("\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
                
        if not is_valid:
            sys.exit(1)
            
    except ImportError as e:
        print(f"Error: JWT security module not available: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error validating secret: {e}")
        sys.exit(1)

def test_system(args):
    """Test JWT security system"""
    try:
        from apps.backend.core.security.jwt import init_jwt_security, get_jwt_security_manager
        from toolboxai_settings.settings import validate_jwt_security
        
        print("🔒 Testing JWT Security System...")
        print("=" * 50)
        
        # Test settings module
        print("\n1. Testing settings module...")
        try:
            security_status = validate_jwt_security()
            print(f"   ✓ Settings loaded: {security_status}")
        except Exception as e:
            print(f"   ✗ Settings error: {e}")
        
        # Test JWT manager
        print("\n2. Testing JWT security manager...")
        try:
            manager = init_jwt_security()
            success, status = manager.initialize()
            print(f"   ✓ Manager initialized: {success}")
            if status.get('warnings'):
                for warning in status['warnings']:
                    print(f"   ⚠️  {warning}")
        except Exception as e:
            print(f"   ✗ Manager error: {e}")
        
        # Test current configuration
        print("\n3. Testing current configuration...")
        try:
            current_secret = os.getenv('JWT_SECRET_KEY', 'NOT_SET')
            if current_secret == 'NOT_SET':
                print("   ⚠️  JWT_SECRET_KEY not set in environment")
            else:
                from apps.backend.core.security.jwt import JWTSecretGenerator
                generator = JWTSecretGenerator()
                is_valid, report = generator.validate_secret(current_secret)
                print(f"   {'✓' if is_valid else '✗'} Current secret: {'Valid' if is_valid else 'Invalid'}")
                if not is_valid and report['issues']:
                    for issue in report['issues'][:3]:  # Show first 3 issues
                        print(f"     • {issue}")
        except Exception as e:
            print(f"   ✗ Configuration test error: {e}")
        
        # Test token operations
        print("\n4. Testing token operations...")
        try:
            from apps.backend.api.auth.db_auth import db_auth
            
            # Test token creation
            test_user = {
                'id': 'test-user-123',
                'username': 'test_user',
                'email': 'test@example.com',
                'role': 'student'
            }
            
            tokens = db_auth.create_tokens(test_user)
            print(f"   ✓ Token creation: Success")
            
            # Test token verification
            payload = db_auth.verify_token(tokens['access_token'])
            if payload:
                print(f"   ✓ Token verification: Success")
                print(f"     User ID: {payload.get('user_id')}")
                print(f"     Role: {payload.get('role')}")
            else:
                print(f"   ✗ Token verification: Failed")
                
        except Exception as e:
            print(f"   ✗ Token operations error: {e}")
        
        # Test security status
        print("\n5. Security status summary...")
        try:
            if 'manager' in locals():
                status = manager.get_security_status()
                print(f"   Security level: {status.get('security_level', 'unknown').upper()}")
                print(f"   Secret configured: {'✓' if status.get('secret_configured') else '✗'}")
                print(f"   Secret valid: {'✓' if status.get('secret_valid') else '✗'}")
        except Exception as e:
            print(f"   ✗ Status check error: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 JWT Security System Test Complete")
        
    except ImportError as e:
        print(f"Error: Required modules not available: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error testing system: {e}")
        sys.exit(1)

def rotate_secret(args):
    """Rotate JWT secret"""
    try:
        from apps.backend.core.security.jwt import init_jwt_security
        
        print("🔄 Rotating JWT Secret...")
        
        manager = init_jwt_security()
        success, report = manager.rotate_secret(force=args.force)
        
        if success:
            print("✓ Secret rotation completed successfully!")
            print(f"  New secret ID: {report.get('new_secret_id')}")
            if report.get('instructions_file'):
                print(f"  Instructions saved to: {report['instructions_file']}")
        else:
            print("✗ Secret rotation failed")
            print(f"  Reason: {report.get('rotation_reason', 'Unknown error')}")
            sys.exit(1)
            
    except ImportError as e:
        print(f"Error: JWT security module not available: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error rotating secret: {e}")
        sys.exit(1)

def status_check(args):
    """Check JWT security status"""
    try:
        from toolboxai_settings.settings import validate_jwt_security
        
        print("🔍 JWT Security Status Check")
        print("=" * 40)
        
        status = validate_jwt_security()
        
        print(f"Secret configured: {'✓' if status.get('secret_configured') else '✗'}")
        print(f"Secret length: {status.get('secret_length', 0)} characters")
        print(f"Environment: {status.get('environment', 'unknown')}")
        
        if status.get('using_fallback'):
            print("⚠️  Using fallback validation (advanced security not available)")
        
        # Try advanced status if available
        try:
            from apps.backend.core.security.jwt import get_jwt_security_manager
            
            manager = get_jwt_security_manager()
            if manager:
                advanced_status = manager.get_security_status()
                print(f"Security level: {advanced_status.get('security_level', 'unknown').upper()}")
                print(f"Secret valid: {'✓' if advanced_status.get('secret_valid') else '✗'}")
                
                if advanced_status.get('recommendations'):
                    print("\n💡 Recommendations:")
                    for rec in advanced_status['recommendations']:
                        print(f"  • {rec}")
        except ImportError:
            pass
        
        print("=" * 40)
        
    except Exception as e:
        print(f"Error checking status: {e}")
        sys.exit(1)

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="JWT Security Management CLI for ToolboxAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate --length 64 --instructions
  %(prog)s validate --secret "your-secret-here"
  %(prog)s validate  # Uses JWT_SECRET_KEY from environment
  %(prog)s test
  %(prog)s rotate --force
  %(prog)s status
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a new JWT secret')
    gen_parser.add_argument('--length', type=int, default=64, 
                           help='Secret length in characters (default: 64)')
    gen_parser.add_argument('--hex', action='store_true', 
                           help='Generate hexadecimal secret')
    gen_parser.add_argument('--base64', action='store_true', 
                           help='Generate base64 encoded secret')
    gen_parser.add_argument('--store', action='store_true', 
                           help='Store secret securely')
    gen_parser.add_argument('--instructions', action='store_true',
                           help='Show deployment instructions')
    gen_parser.set_defaults(func=generate_secret)
    
    # Validate command
    val_parser = subparsers.add_parser('validate', help='Validate a JWT secret')
    val_parser.add_argument('--secret', type=str,
                           help='Secret to validate (or use JWT_SECRET_KEY env var)')
    val_parser.set_defaults(func=validate_secret)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test JWT security system')
    test_parser.set_defaults(func=test_system)
    
    # Rotate command
    rotate_parser = subparsers.add_parser('rotate', help='Rotate JWT secret')
    rotate_parser.add_argument('--force', action='store_true',
                              help='Force rotation even if current secret is valid')
    rotate_parser.set_defaults(func=rotate_secret)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check JWT security status')
    status_parser.set_defaults(func=status_check)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.verbose)
    
    # Execute the selected command
    args.func(args)

if __name__ == '__main__':
    main()
