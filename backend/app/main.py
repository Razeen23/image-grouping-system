"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import upload, images, faces, groups, processing

# Create FastAPI app
app = FastAPI(
    title="Face Recognition Photo Grouping API",
    description="API for grouping photos by detected faces",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(images.router)
app.include_router(faces.router)
app.include_router(groups.router)
app.include_router(processing.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Face Recognition Photo Grouping API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
