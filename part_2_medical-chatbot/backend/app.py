import os
import sys
import glob
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from backend.config import settings, RAW_COMBINED_HTML_PATH, KNOWLEDGE_BASE_DIR
from backend.routers import chat, health
from backend.utils.logging_config import setup_logging
from data.HMO_preprocessor import preprocess_hmo_html
from backend.routers.extraction import router as extraction_router
from backend.routers.chat import router as chat_router


logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Medical Services Chatbot API starting up")

    # Ensure directories exist
    input_dir = Path("data/phase2_data")
    output_dir = Path("data/preprocessed_hmo")
    
    # Create directories if they don't exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Input directory: {input_dir.absolute()}")
    logger.info(f"Output directory: {output_dir.absolute()}")
    
    # Check for input files
    input_files = list(input_dir.glob("*.html"))
    logger.info(f"Found {len(input_files)} input HTML files")
    
    try:
        # Preprocess data if there are input files
        if input_files:
            result = preprocess_hmo_html(
                input_dir=str(input_dir), 
                output_dir=str(output_dir)
            )
            logger.info(f"Preprocessing result: {result}")
        else:
            logger.warning("No input HTML files found, skipping preprocessing")
        
        # Check for output files
        output_files = list(output_dir.glob("*.html"))
        logger.info(f"Found {len(output_files)} preprocessed HTML files: {[f.name for f in output_files]}")
        
        # Make sure KNOWLEDGE_BASE_DIR points to the right location
        logger.info(f"Knowledge base directory set to: {KNOWLEDGE_BASE_DIR}")
        
        # Create a symlink if KNOWLEDGE_BASE_DIR is different from output_dir
        kb_dir = Path(KNOWLEDGE_BASE_DIR)
        if kb_dir.absolute() != output_dir.absolute():
            logger.info(f"Creating symbolic link from {output_dir.absolute()} to {kb_dir.absolute()}")
            kb_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files instead of symlink (more reliable)
            for file in output_files:
                target = kb_dir / file.name
                if not target.exists():
                    import shutil
                    shutil.copy2(file, target)
                    logger.info(f"Copied {file.name} to {target}")
    
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        # Log the full traceback
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    yield
    
    logger.info("Medical Services Chatbot API shutting down")


app = FastAPI(
    title="Medical Services Chatbot API",
    description="A microservice for answering questions about Israeli health funds",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(extraction_router, prefix="/api/chat", tags=["chat"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    logger.error(f"Request path: {request.url.path}")
    
    # Get traceback
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."}
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)