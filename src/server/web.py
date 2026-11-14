import os
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from src.storage.logger import audit_logger
from src.server.templates import DASHBOARD_HTML

web_app = FastAPI(
    title="Data Analyst Agent Telemetry & Log Server",
    description="Live telemetry, health checks, and public audit log endpoints.",
    version="1.0.0",
)

# Enable CORS for public graders and API consumers
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@web_app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Live Visual Telemetry & Monitoring Dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)

@web_app.get("/health")
async def health_check():
    """Health check endpoint for Render/Railway/Fly.io/UptimeRobot keep-alive."""
    return {"status": "ok", "service": "data-analyst-agent"}

@web_app.get("/run.jsonl")
async def download_run_log():
    """
    Public raw log endpoint required by TDS grading pipeline and external monitors.
    Returns the real-time run.jsonl file directly via HTTP/wget.
    """
    if not os.path.exists(settings.log_file):
        return Response(content="", media_type="text/plain")

    return FileResponse(
        path=settings.log_file,
        media_type="text/plain",
        filename="run.jsonl",
    )

@web_app.get("/api/stats")
async def get_stats():
    """Telemetry data consumed by the dashboard UI."""
    return {
        "stats": audit_logger.get_stats(),
        "logs": audit_logger.get_recent_logs(limit=30),
    }
