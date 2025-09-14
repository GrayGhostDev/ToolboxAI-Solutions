"""
Test Logger Configuration
Centralized logging configuration for all tests with structured output
"""

import logging
import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import wraps
import pytest

# Ensure test log directory exists
TEST_LOG_DIR = Path(__file__).parent / "logs"
TEST_LOG_DIR.mkdir(exist_ok=True)

# Create subdirectories
for subdir in ["unit", "integration", "e2e", "debug", "reports"]:
    (TEST_LOG_DIR / subdir).mkdir(exist_ok=True)

class TestLogger:
    """Enhanced test logger with structured output and test tracking"""
    
    def __init__(self, name: str, test_type: str = "unit"):
        self.name = name
        self.test_type = test_type
        self.logger = self._setup_logger()
        self.test_results: List[Dict[str, Any]] = []
        self.current_test: Optional[str] = None
        self.correlation_id: Optional[str] = None
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with multiple handlers for different outputs"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)8s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # File Handler - General log
        log_dir = TEST_LOG_DIR / f"{self.test_type}"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)8s] [%(filename)s:%(lineno)d] %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        file_handler.setFormatter(file_format)
        
        # Debug Handler - Detailed debug log
        debug_dir = TEST_LOG_DIR / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_file = debug_dir / f"debug_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        debug_handler = logging.FileHandler(debug_file)
        debug_handler.setLevel(logging.DEBUG)
        debug_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] [%(pathname)s:%(lineno)d] '
            '[%(funcName)s] [PID:%(process)d] [Thread:%(thread)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        debug_handler.setFormatter(debug_format)
        
        # JSON Handler - Structured logs for analysis
        reports_dir = TEST_LOG_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        json_file = reports_dir / f"structured_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.json_file = json_file
        self.json_handler = JsonFileHandler(json_file)
        self.json_handler.setLevel(logging.DEBUG)
        
        # Add all handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(debug_handler)
        logger.addHandler(self.json_handler)
        
        return logger
    
    def start_test(self, test_name: str, correlation_id: Optional[str] = None):
        """Mark the start of a test"""
        self.current_test = test_name
        self.correlation_id = correlation_id or f"test_{datetime.now().timestamp()}"
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Starting test: {test_name}")
        self.logger.info(f"Correlation ID: {self.correlation_id}")
        self.logger.info(f"{'='*80}")
        
    def end_test(self, test_name: str, status: str, duration: float = 0.0, error: Optional[str] = None):
        """Mark the end of a test"""
        result = {
            "test_name": test_name,
            "status": status,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": self.correlation_id,
            "error": error
        }
        self.test_results.append(result)
        
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Test completed: {test_name}")
        self.logger.info(f"Status: {status}")
        self.logger.info(f"Duration: {duration:.3f}s")
        if error:
            self.logger.error(f"Error: {error}")
        self.logger.info(f"{'='*80}")
        
        self.current_test = None
        self.correlation_id = None
        
    def log_assertion(self, condition: bool, message: str, expected: Any = None, actual: Any = None):
        """Log an assertion with details"""
        if condition:
            self.logger.debug(f"✓ Assertion passed: {message}")
        else:
            self.logger.error(f"✗ Assertion failed: {message}")
            if expected is not None:
                self.logger.error(f"  Expected: {expected}")
            if actual is not None:
                self.logger.error(f"  Actual: {actual}")
                
    def log_exception(self, exc: Exception, context: Optional[str] = None):
        """Log an exception with full traceback"""
        self.logger.error(f"Exception occurred: {type(exc).__name__}: {str(exc)}")
        if context:
            self.logger.error(f"Context: {context}")
        self.logger.error(f"Traceback:\n{traceback.format_exc()}")
        
    def generate_report(self):
        """Generate a test report"""
        report_file = TEST_LOG_DIR / "reports" / f"test_report_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "passed")
        failed = sum(1 for r in self.test_results if r["status"] == "failed")
        skipped = sum(1 for r in self.test_results if r["status"] == "skipped")
        
        report = {
            "test_suite": self.name,
            "test_type": self.test_type,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0
            },
            "results": self.test_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Test report generated: {report_file}")
        return report
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.log_exception(exc_val)
        self.generate_report()

class JsonFileHandler(logging.Handler):
    """Custom handler for structured JSON logging"""
    
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename
        self.logs = []
        
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.thread,
        }
        
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
            
        if record.exc_info:
            log_entry['exception'] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        self.logs.append(log_entry)
        
        # Write to file
        with open(self.filename, 'w') as f:
            json.dump(self.logs, f, indent=2)

def log_test_execution(test_type: str = "unit"):
    """Decorator for automatic test logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = TestLogger(func.__module__, test_type)
            test_name = f"{func.__module__}.{func.__name__}"
            
            logger.start_test(test_name)
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.end_test(test_name, "passed", duration)
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.end_test(test_name, "failed", duration, str(e))
                raise
                
        return wrapper
    return decorator

# Pytest fixtures for test logging
@pytest.fixture
def test_logger(request):
    """Pytest fixture for test logging"""
    test_name = request.node.name
    test_module = request.module.__name__
    test_type = "unit"  # Default
    
    # Determine test type from markers
    if request.node.get_closest_marker("integration"):
        test_type = "integration"
    elif request.node.get_closest_marker("e2e"):
        test_type = "e2e"
        
    logger = TestLogger(test_module, test_type)
    logger.start_test(test_name)
    
    yield logger
    
    # Determine test outcome
    if hasattr(request.node, 'rep_call'):
        if request.node.rep_call.failed:
            logger.end_test(test_name, "failed", error=str(request.node.rep_call.longrepr))
        elif request.node.rep_call.passed:
            logger.end_test(test_name, "passed")
        elif request.node.rep_call.skipped:
            logger.end_test(test_name, "skipped")
    else:
        logger.end_test(test_name, "unknown")

# Configure root logger for tests
def configure_test_logging():
    """Configure root logging for all tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)8s] [%(name)s] %(message)s',
        handlers=[
            logging.FileHandler(TEST_LOG_DIR / "all_tests.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

# Auto-configure on import
configure_test_logging()

# Export main components
__all__ = ['TestLogger', 'log_test_execution', 'test_logger', 'TEST_LOG_DIR']