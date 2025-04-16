from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from config import settings
from routes import chat, health
from utils.logging_config import setup_logging
from contextlib import asynccontextmanager

logger = setup_logging()

app = FastAPI(
    title="Medical Services Chatbot API",
    description="A microservice for answering questions about Israeli health funds",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  ## allwing all origins, of course, it's only good for development and not good for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"]) ## the api prefix is only for distinguishing the API routes from frontend routes


@app.exception_handler(Exception) ## catches any unhandled error
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."}
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Medical Services Chatbot API starting up")
    yield
    logger.info("Medical Services Chatbot API shutting down")

app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)