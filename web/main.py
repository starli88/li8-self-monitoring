"""
Accountability Dashboard - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from .routers import api, views

app = FastAPI(
    title="Accountability Dashboard",
    description="داشبورد نظارت بر محتوا",
    version="1.0.0"
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(api.router)
app.include_router(views.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
