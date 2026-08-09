"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.api import trade, rate, scenario, trader

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="FX Trade Simulation API",
    description="Foreign Exchange Trading Simulation Server",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trade.router, prefix=f"{settings.api_prefix}/trade", tags=["Trade"])
app.include_router(rate.router, prefix=f"{settings.api_prefix}/rate", tags=["Rate"])
app.include_router(scenario.router, prefix=f"{settings.api_prefix}/scenario", tags=["Scenario"])
app.include_router(trader.router, prefix=f"{settings.api_prefix}/trader", tags=["Trader"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FX Trade Simulation API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
