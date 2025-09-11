"""
Main FastAPI Application for Educational Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Ghost framework is now installed as a package

# Import routers
from api.education import router as education_router
from api.auth import router as auth_router
from api.classes import router as classes_router
from api.assessments import router as assessments_router
from api.messages import router as messages_router
from api.progress import router as progress_router
from api.compliance import router as compliance_router
from api.schools import router as schools_router
from api.users import router as users_router
from api.reports import router as reports_router

# Import WebSocket server
from websocket import socket_app, sio

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Educational Platform Backend...")
    yield
    # Shutdown
    print("👋 Shutting down Educational Platform Backend...")

# Create FastAPI app
app = FastAPI(
    title="ToolBoxAI Educational Platform API",
    description="Backend API for Roblox Educational Training Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "https://d3vhlb3c-5173.use.devtunnels.ms",
        "https://d3vhlb3c-3000.use.devtunnels.ms",
        "https://d3vhlb3c-8001.use.devtunnels.ms",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Educational Platform API",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ToolBoxAI Educational Platform API",
        "documentation": "/api/docs",
        "health": "/health"
    }

# Include routers
app.include_router(auth_router)
app.include_router(education_router)
app.include_router(classes_router)
app.include_router(schools_router)
app.include_router(users_router)
app.include_router(assessments_router)
app.include_router(messages_router)
app.include_router(progress_router)
app.include_router(compliance_router)
app.include_router(reports_router)

# Mount Socket.IO application
app.mount("/", socket_app)

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )