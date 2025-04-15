from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime

# Import configuration and routes
from config import settings
from routes import chat, health
from utils.logging_config import setup_logging

# Initialize logger
logger = setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Medical Services Chatbot API",
    description="A microservice for answering questions about Israeli health funds",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Medical Services Chatbot API starting up")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Medical Services Chatbot API shutting down")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)