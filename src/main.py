#!/usr/bin/env python3
"""
IZA OS Project Management Analytics Bot
Main application entry point for project analytics and intelligence.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add src to path
sys.path.append(str(Path(__file__).parent))

from analytics.project_analytics import ProjectAnalyzer
from analytics.portfolio_optimization import PortfolioOptimizer
from analytics.risk_assessment import RiskAnalyzer
from data.collectors.project_data_collector import ProjectDataCollector
from api.endpoints.projects import router as projects_router
from api.endpoints.portfolio import router as portfolio_router
from api.endpoints.health import router as health_router
from config.project_config import ProjectConfig
from utils.logging_config import setup_logging


# Global instances
project_analyzer: ProjectAnalyzer = None
portfolio_optimizer: PortfolioOptimizer = None
risk_analyzer: RiskAnalyzer = None
data_collector: ProjectDataCollector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global project_analyzer, portfolio_optimizer, risk_analyzer, data_collector
    
    # Startup
    logging.info("🚀 Starting IZA OS Project Management Analytics Bot...")
    
    try:
        # Initialize configuration
        config = ProjectConfig()
        
        # Initialize core components
        data_collector = ProjectDataCollector(config)
        project_analyzer = ProjectAnalyzer(config, data_collector)
        portfolio_optimizer = PortfolioOptimizer(config, data_collector)
        risk_analyzer = RiskAnalyzer(config, data_collector)
        
        # Start data collection
        await data_collector.start()
        
        # Initialize AI models
        await project_analyzer.load_models()
        
        logging.info("✅ Project Management Analytics Bot initialized successfully")
        
    except Exception as e:
        logging.error(f"❌ Failed to initialize Project Analytics Bot: {e}")
        raise
    
    yield
    
    # Shutdown
    logging.info("🛑 Shutting down Project Management Analytics Bot...")
    
    if data_collector:
        await data_collector.stop()
    
    logging.info("✅ Project Management Analytics Bot shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Setup logging
    setup_logging()
    
    app = FastAPI(
        title="IZA OS Project Management Analytics Bot",
        description="Advanced AI-powered project management analytics and intelligence bot",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(portfolio_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/api/v1")
    
    # WebSocket connections
    active_connections: Dict[str, WebSocket] = {}
    
    @app.websocket("/ws/projects")
    async def websocket_projects(websocket: WebSocket):
        """WebSocket endpoint for real-time project updates."""
        await websocket.accept()
        connection_id = f"projects_{id(websocket)}"
        active_connections[connection_id] = websocket
        
        try:
            while True:
                # Send real-time project data
                if project_analyzer:
                    project_data = await project_analyzer.get_realtime_analytics()
                    await websocket.send_json(project_data)
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except WebSocketDisconnect:
            active_connections.pop(connection_id, None)
            logging.info(f"WebSocket connection {connection_id} disconnected")
    
    @app.websocket("/ws/portfolio")
    async def websocket_portfolio(websocket: WebSocket):
        """WebSocket endpoint for real-time portfolio updates."""
        await websocket.accept()
        connection_id = f"portfolio_{id(websocket)}"
        active_connections[connection_id] = websocket
        
        try:
            while True:
                # Send real-time portfolio data
                if portfolio_optimizer:
                    portfolio_data = await portfolio_optimizer.get_realtime_portfolio()
                    await websocket.send_json(portfolio_data)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except WebSocketDisconnect:
            active_connections.pop(connection_id, None)
            logging.info(f"WebSocket connection {connection_id} disconnected")
    
    @app.websocket("/ws/alerts")
    async def websocket_alerts(websocket: WebSocket):
        """WebSocket endpoint for project alerts and notifications."""
        await websocket.accept()
        connection_id = f"alerts_{id(websocket)}"
        active_connections[connection_id] = websocket
        
        try:
            while True:
                # Send project alerts
                if risk_analyzer:
                    alerts = await risk_analyzer.get_active_alerts()
                    if alerts:
                        await websocket.send_json(alerts)
                
                await asyncio.sleep(10)  # Check alerts every 10 seconds
                
        except WebSocketDisconnect:
            active_connections.pop(connection_id, None)
            logging.info(f"WebSocket connection {connection_id} disconnected")
    
    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        return {
            "service": "IZA OS Project Management Analytics Bot",
            "version": "1.0.0",
            "status": "operational",
            "description": "Advanced AI-powered project management analytics and intelligence bot",
            "endpoints": {
                "projects": "/api/v1/projects",
                "portfolio": "/api/v1/portfolio",
                "health": "/api/v1/health",
                "websocket_projects": "/ws/projects",
                "websocket_portfolio": "/ws/portfolio",
                "websocket_alerts": "/ws/alerts"
            }
        }
    
    return app


def main():
    """Main entry point."""
    app = create_app()
    
    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
