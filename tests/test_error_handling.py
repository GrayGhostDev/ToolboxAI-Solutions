"""
Test Comprehensive Error Handling

Verifies that the error handling system works correctly across different
error types and scenarios.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# Import error handling components
from apps.backend.core.errors import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConfigurationError,
    DatabaseError,
    ErrorCategory,
    ErrorDetail,
    ErrorHandler,
    ErrorResponse,
    ErrorSeverity,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    handle_application_error,
    handle_generic_exception,
    handle_http_exception,
    handle_validation_error,
)


def create_test_app():
    """Create a test FastAPI app with error handlers and test endpoints"""
    app = FastAPI()
    
    # Initialize app state for error handlers
    app.state.debug = False  # Set to False to test production error handling
    
    # Add exception handlers - order matters, most specific first
    app.add_exception_handler(ApplicationError, handle_application_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(ValueError, handle_generic_exception)  # Explicitly handle ValueError
    app.add_exception_handler(RuntimeError, handle_generic_exception)  # Explicitly handle RuntimeError
    app.add_exception_handler(Exception, handle_generic_exception)  # Catch-all for other exceptions
    
    # Test models
    class TestRequest(BaseModel):
        name: str = Field(..., min_length=3, max_length=50)
        age: int = Field(..., ge=0, le=150)
        email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    
    # Test endpoints
    @app.post("/test/validation")
    @pytest.mark.asyncio(loop_scope="function")
    async def test_validation(data: TestRequest):
        return {"message": "Valid data", "data": data.model_dump()}
    
    @app.get("/test/auth")
    async def test_auth():
        raise AuthenticationError("Invalid token")
    
    @app.get("/test/authz")
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio(loop_scope="function")
    async def test_authz():
        raise AuthorizationError("Admin access required")
    
    @app.get("/test/not-found/{item_id}")
    async def test_not_found(item_id: str):
        raise NotFoundError("Item", item_id)
    
    @app.get("/test/conflict")
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio(loop_scope="function")
    async def test_conflict():
        raise ConflictError("Resource already exists")
    
    @app.get("/test/rate-limit")
    async def test_rate_limit():
        raise RateLimitError("Too many requests", retry_after=60)
    
    @app.get("/test/database")
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio(loop_scope="function")
    async def test_database():
        raise DatabaseError("Connection failed", operation="SELECT")
    
    @app.get("/test/external")
    async def test_external():
        raise ExternalServiceError("PaymentAPI", "Timeout")
    
    @app.get("/test/http-exception")
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio(loop_scope="function")
    async def test_http_exception():
        raise HTTPException(status_code=400, detail="Bad request")
    
    @app.get("/test/value-error")
    async def test_value_error():
        raise ValueError("Invalid value provided")
    
    @app.get("/test/generic-error")
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio(loop_scope="function")
    async def test_generic_error():
        raise RuntimeError("Unexpected runtime error")
    
    return app


class TestErrorTypes:
    """Test different error types"""
    
    def setup_method(self):
        """Setup test client"""
        self.app = create_test_app()
        self.client = TestClient(self.app)
    
    def test_validation_error_request(self):
        """Test request validation error"""
        response = self.client.post("/test/validation", json={
            "name": "ab",  # Too short
            "age": 200,  # Too high
            "email": "invalid-email"  # Invalid format
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"
        assert data["message"] == "Request validation failed"
        assert len(data["details"]) == 3
        
        # Check error details
        fields = {detail["field"] for detail in data["details"]}
        assert "name" in fields
        assert "age" in fields
        assert "email" in fields
    
    def test_authentication_error(self):
        """Test authentication error"""
        response = self.client.get("/test/auth")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "authentication"
        assert data["message"] == "Invalid token"
        assert "error_id" in data
        assert "X-Error-ID" in response.headers
    
    def test_authorization_error(self):
        """Test authorization error"""
        response = self.client.get("/test/authz")
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "authorization"
        assert data["message"] == "Admin access required"
    
    def test_not_found_error(self):
        """Test not found error"""
        response = self.client.get("/test/not-found/12345")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "not_found"
        assert data["message"] == "Item not found: 12345"
    
    def test_conflict_error(self):
        """Test conflict error"""
        response = self.client.get("/test/conflict")
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "conflict"
        assert data["message"] == "Resource already exists"
    
    def test_rate_limit_error(self):
        """Test rate limit error"""
        response = self.client.get("/test/rate-limit")
        
        assert response.status_code == 429
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "rate_limit"
        assert data["message"] == "Too many requests"
        assert response.headers.get("Retry-After") == "60"
    
    def test_database_error(self):
        """Test database error"""
        response = self.client.get("/test/database")
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "database"
        assert data["message"] == "Connection failed"
        assert len(data["details"]) == 1
        assert data["details"][0]["message"] == "Operation: SELECT"
    
    def test_external_service_error(self):
        """Test external service error"""
        response = self.client.get("/test/external")
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "external_service"
        assert "PaymentAPI" in data["message"]
        assert "Timeout" in data["message"]
    
    def test_http_exception(self):
        """Test standard HTTP exception"""
        response = self.client.get("/test/http-exception")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"
        assert data["message"] == "Bad request"
    
    def test_value_error(self):
        """Test value error handling"""
        response = self.client.get("/test/value-error")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"
        # In production mode (debug=False), sensitive error details are hidden
        assert data["message"] == "Invalid input provided"
        assert "error_id" in data
        assert "timestamp" in data
    
    def test_generic_error(self):
        """Test generic error handling"""
        response = self.client.get("/test/generic-error")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "internal"
        # In production mode (debug=False), internal error details are hidden
        assert data["message"] == "An internal error occurred"
        assert "error_id" in data
        assert "timestamp" in data
        assert "correlation_id" in data


class TestErrorHandler:
    """Test ErrorHandler functionality"""
    
    def test_error_handler_initialization(self):
        """Test error handler initialization"""
        handler = ErrorHandler(debug=False)
        assert handler.debug is False
        assert len(handler.error_mappers) > 0
    
    def test_error_handler_debug_mode(self):
        """Test error handler in debug mode"""
        handler = ErrorHandler(debug=True)
        assert handler.debug is True
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_error_response_format(self):
        """Test error response format"""
        handler = ErrorHandler(debug=False)
        
        # Create mock request with proper state
        request = Mock(spec=Request)
        request.url.path = "/test/path"
        request.method = "GET"
        request.state = Mock()
        request.state.correlation_id = None  # Set to None instead of leaving as Mock
        request.app.state = Mock(debug=False)
        
        # Create test error
        error = ValidationError("Test validation error")
        
        # Handle error
        response = await handler.handle_error(request, error)
        
        # Check response
        assert response.status_code == 422
        assert "X-Error-ID" in response.headers
        assert "X-Correlation-ID" in response.headers
        
        # Parse response body
        data = json.loads(response.body)
        assert data["error"] is True
        assert data["status_code"] == 422
        assert data["category"] == "validation"
        assert data["message"] == "Test validation error"
        assert data["path"] == "/test/path"
        assert data["method"] == "GET"
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_correlation_id_propagation(self):
        """Test correlation ID propagation"""
        handler = ErrorHandler(debug=False)
        
        # Create mock request with correlation ID
        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        request.state = Mock()
        request.state.correlation_id = "test-correlation-id"
        request.app.state = Mock(debug=False)
        
        # Handle error
        error = AuthenticationError()
        response = await handler.handle_error(request, error)
        
        # Check correlation ID in response
        assert response.headers["X-Correlation-ID"] == "test-correlation-id"
        data = json.loads(response.body)
        assert data["correlation_id"] == "test-correlation-id"
    
    def test_error_category_mapping(self):
        """Test status code to category mapping"""
        handler = ErrorHandler()
        
        assert handler._map_status_to_category(400) == ErrorCategory.VALIDATION
        assert handler._map_status_to_category(401) == ErrorCategory.AUTHENTICATION
        assert handler._map_status_to_category(403) == ErrorCategory.AUTHORIZATION
        assert handler._map_status_to_category(404) == ErrorCategory.NOT_FOUND
        assert handler._map_status_to_category(409) == ErrorCategory.CONFLICT
        assert handler._map_status_to_category(422) == ErrorCategory.VALIDATION
        assert handler._map_status_to_category(429) == ErrorCategory.RATE_LIMIT
        assert handler._map_status_to_category(500) == ErrorCategory.INTERNAL
        assert handler._map_status_to_category(503) == ErrorCategory.EXTERNAL_SERVICE


class TestErrorModels:
    """Test error model classes"""
    
    def test_error_detail_model(self):
        """Test ErrorDetail model"""
        detail = ErrorDetail(
            field="username",
            message="Username already exists",
            code="unique_constraint",
            context={"existing_value": "john_doe"}
        )
        
        assert detail.field == "username"
        assert detail.message == "Username already exists"
        assert detail.code == "unique_constraint"
        assert detail.context["existing_value"] == "john_doe"
    
    def test_error_response_model(self):
        """Test ErrorResponse model"""
        response = ErrorResponse(
            status_code=400,
            category=ErrorCategory.VALIDATION,
            message="Validation failed",
            details=[
                ErrorDetail(field="email", message="Invalid email format")
            ]
        )
        
        assert response.error is True
        assert response.status_code == 400
        assert response.category == ErrorCategory.VALIDATION
        assert response.message == "Validation failed"
        assert len(response.details) == 1
        assert response.error_id is not None
        assert response.timestamp is not None
    
    def test_application_error_hierarchy(self):
        """Test application error hierarchy"""
        # Base error
        base_error = ApplicationError("Base error")
        assert base_error.status_code == 500
        assert base_error.category == ErrorCategory.INTERNAL
        
        # Validation error
        val_error = ValidationError("Validation failed")
        assert val_error.status_code == 422
        assert val_error.category == ErrorCategory.VALIDATION
        assert val_error.severity == ErrorSeverity.LOW
        
        # Authentication error
        auth_error = AuthenticationError()
        assert auth_error.status_code == 401
        assert auth_error.category == ErrorCategory.AUTHENTICATION
        assert auth_error.severity == ErrorSeverity.MEDIUM


class TestErrorRecovery:
    """Test error recovery patterns"""
    
    def test_error_with_details(self):
        """Test error with detailed information"""
        details = [
            ErrorDetail(
                field="password",
                message="Password must be at least 8 characters",
                code="min_length"
            ),
            ErrorDetail(
                field="password",
                message="Password must contain a number",
                code="pattern"
            )
        ]
        
        error = ValidationError("Password validation failed", details=details)
        assert len(error.details) == 2
        assert error.details[0].field == "password"
    
    def test_database_error_with_operation(self):
        """Test database error with operation context"""
        error = DatabaseError("Connection timeout", operation="INSERT INTO users")
        assert error.status_code == 503
        assert error.category == ErrorCategory.DATABASE
        assert len(error.details) == 1
        assert "INSERT INTO users" in error.details[0].message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])