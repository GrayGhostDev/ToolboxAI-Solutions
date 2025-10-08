"""
Tenant Middleware for ToolBoxAI Educational Platform

This middleware is responsible for identifying the tenant based on the request
and setting the tenant context for the rest of the application.

Author: ToolBoxAI Team
Created: 2025-10-06
Version: 1.0.0
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseFunction
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseFunction) -> Response:
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id:
            # This is a temporary measure to allow requests that don't have a tenant ID.
            # In a production environment, you would want to raise an exception here.
            logger.warning("X-Tenant-ID header not found. Proceeding without tenant context.")
            response = await call_next(request)
            return response

        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response
