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