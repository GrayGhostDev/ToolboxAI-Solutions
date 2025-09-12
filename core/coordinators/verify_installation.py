"""
Coordinator System Installation Verification

Verifies that all coordinator components are properly installed and configured.
"""

import sys
import os
import importlib
from pathlib import Path
from typing import List, Dict, Any

def check_python_version() -> bool:
    """Check if Python version is compatible"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version >= required_version:
        print(f"✓ Python version: {sys.version.split()[0]} (required: {'.'.join(map(str, required_version))}+)")
        return True
    else:
        print(f"✗ Python version: {sys.version.split()[0]} (required: {'.'.join(map(str, required_version))}+)")
        return False

def check_required_packages() -> bool:
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'websockets',
        'pydantic',
        'langchain',
        'psutil',
        'yaml'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            # Try different import names
            import_names = {
                'yaml': 'yaml',
                'langchain': 'langchain',
                'fastapi': 'fastapi',
                'uvicorn': 'uvicorn',
                'websockets': 'websockets',
                'pydantic': 'pydantic',
                'psutil': 'psutil'
            }
            
            import_name = import_names.get(package, package)
            importlib.import_module(import_name)
            installed_packages.append(package)
            print(f"✓ {package}")
            
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} (not installed)")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_coordinator_files() -> bool:
    """Check if all coordinator files are present"""
    coordinator_dir = Path(__file__).parent
    
    required_files = [
        '__init__.py',
        'main_coordinator.py',
        'workflow_coordinator.py',
        'resource_coordinator.py',
        'sync_coordinator.py',
        'error_coordinator.py',
        'config.py'
    ]
    
    missing_files = []
    present_files = []
    
    for file_name in required_files:
        file_path = coordinator_dir / file_name
        if file_path.exists():
            present_files.append(file_name)
            print(f"✓ {file_name}")
        else:
            missing_files.append(file_name)
            print(f"✗ {file_name} (missing)")
    
    if missing_files:
        print(f"\nMissing files: {', '.join(missing_files)}")
        return False
    
    return True

def check_coordinator_imports() -> bool:
    """Check if coordinator modules can be imported"""
    coordinator_modules = [
        'main_coordinator',
        'workflow_coordinator',
        'resource_coordinator',
        'sync_coordinator',
        'error_coordinator',
        'config'
    ]
    
    import_errors = []
    successful_imports = []
    
    # Add current directory to path for testing
    coordinator_dir = Path(__file__).parent
    if str(coordinator_dir.parent) not in sys.path:
        sys.path.insert(0, str(coordinator_dir.parent))
    
    for module_name in coordinator_modules:
        try:
            module = importlib.import_module(f'coordinators.{module_name}')
            successful_imports.append(module_name)
            print(f"✓ coordinators.{module_name}")
            
        except ImportError as e:
            import_errors.append((module_name, str(e)))
            print(f"✗ coordinators.{module_name} (import error: {e})")
        except Exception as e:
            import_errors.append((module_name, str(e)))
            print(f"✗ coordinators.{module_name} (error: {e})")
    
    if import_errors:
        print(f"\nImport errors found in {len(import_errors)} modules")
        return False
    
    return True

def check_integration_components() -> bool:
    """Check if integration components are available"""
    components_to_check = [
        ('agents', 'agents'),
        ('swarm', 'swarm'),
        ('sparc', 'sparc'),
        ('mcp', 'mcp')
    ]
    
    available_components = []
    missing_components = []
    
    project_root = Path(__file__).parent.parent
    
    for component_name, directory in components_to_check:
        component_dir = project_root / directory
        
        if component_dir.exists() and (component_dir / '__init__.py').exists():
            available_components.append(component_name)
            print(f"✓ {component_name} system available")
        else:
            missing_components.append(component_name)
            print(f"⚠ {component_name} system not available (will run in limited mode)")
    
    # Not a failure if some components are missing - system can run in degraded mode
    return True

def check_configuration() -> bool:
    """Check if configuration can be loaded"""
    try:
        from coordinators.config import ConfigurationManager, get_development_config
        
        # Test configuration loading
        config_manager = ConfigurationManager()
        config = get_development_config()
        
        print("✓ Configuration loading successful")
        print(f"  Environment: {config.environment}")
        print(f"  Log level: {config.log_level}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def run_basic_functionality_test() -> bool:
    """Run basic functionality test"""
    try:
        print("Running basic functionality test...")
        
        # Test coordinator system import
        from coordinators import CoordinatorSystem
        
        # Test config creation
        from coordinators.config import get_development_config
        config = get_development_config()
        
        print("✓ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def generate_verification_report() -> Dict[str, Any]:
    """Generate comprehensive verification report"""
    
    print("ToolboxAI Coordinator System Installation Verification")
    print("=" * 60)
    
    # Run all checks
    checks = {
        'python_version': check_python_version(),
        'required_packages': check_required_packages(),
        'coordinator_files': check_coordinator_files(),
        'coordinator_imports': check_coordinator_imports(),
        'integration_components': check_integration_components(),
        'configuration': check_configuration(),
        'basic_functionality': run_basic_functionality_test()
    }
    
    print("\n" + "=" * 60)
    
    # Calculate results
    total_checks = len(checks)
    passed_checks = sum(1 for result in checks.values() if result)
    success_rate = (passed_checks / total_checks) * 100
    
    # Print summary
    print(f"Verification Summary: {passed_checks}/{total_checks} checks passed ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 All checks passed! Coordinator system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python coordinators/coordinator_example.py")
        print("2. Or: python coordinators/integration_test.py")
    elif success_rate >= 80:
        print("⚠️  Most checks passed. System should work with limitations.")
        print("Review failed checks above for details.")
    else:
        print("❌ Multiple checks failed. Please resolve issues before using.")
    
    # Generate detailed report
    report = {
        'verification_time': str(Path(__file__).stat().st_mtime),
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'success_rate': success_rate,
        'check_results': checks,
        'system_info': {
            'python_version': sys.version,
            'platform': sys.platform,
            'coordinator_dir': str(Path(__file__).parent)
        }
    }
    
    return report

def main():
    """Main verification function"""
    try:
        report = generate_verification_report()
        
        # Save report to file
        report_file = Path(__file__).parent / "verification_report.json"
        with open(report_file, 'w') as f:
            import json
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        # Exit with appropriate code
        if report['success_rate'] >= 90:
            sys.exit(0)
        else:
            sys.exit(1)
        
    except Exception as e:
        print(f"Verification failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()