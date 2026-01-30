# Face Recognition Photo Grouping Dashboard

A web-based dashboard that automatically groups photos by detected faces, similar to Google Photos "People" feature.

## Features

- **Face Detection**: Automatically detects all faces in uploaded images using InsightFace
- **Face Grouping**: Groups faces by person using cosine similarity matching
- **Group Photos**: Supports photos with multiple faces, linking them to multiple person groups
- **Face-Centric Architecture**: Faces are the primary entity, enabling flexible grouping
- **Background Processing**: Async processing of images for better performance
- **Modern UI**: React + TypeScript frontend with Tailwind CSS

## Architecture

- **Backend**: FastAPI (Python) with InsightFace for face detection
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **Object Storage**: MinIO (S3-compatible) for image storage
- **Frontend**: React + TypeScript + Vite + Tailwind CSS

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 12+ with pgvector extension
- MinIO (or S3-compatible storage)
- Redis (optional, for Celery)

## Setup

### 1. Database Setup

```bash
# Install PostgreSQL 17 or 18 (pgvector requires PostgreSQL 12+, but Homebrew pgvector supports 17+)
# Note: PostgreSQL 14 is deprecated and not supported by Homebrew pgvector
brew install postgresql@17
# OR
brew install postgresql@18

# Start PostgreSQL service
brew services start postgresql@17  # or postgresql@18

# Install pgvector extension
brew install pgvector

# Restart PostgreSQL to load the extension
brew services restart postgresql@17  # or postgresql@18

# Create database
createdb face_groups

# Connect to database and enable extension
psql face_groups
CREATE EXTENSION vector;
\q
```

**Note**: If you have PostgreSQL 14 installed, you'll need to upgrade:
```bash
# Stop old PostgreSQL
brew services stop postgresql@14

# Install newer version
brew install postgresql@17
brew services start postgresql@17

# Install pgvector (if not already installed)
brew install pgvector
brew services restart postgresql@17

# Recreate database
dropdb face_groups  # if it exists
createdb face_groups
psql face_groups -c "CREATE EXTENSION vector;"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# If you hit an onnxruntime install error on macOS, first upgrade pip inside the venv:
# python -m pip install --upgrade pip
# (This repo selects a compatible onnxruntime version based on your Python version.)

# Copy environment file
cp env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. MinIO Setup

```bash
# Install MinIO (macOS)
brew install minio/stable/minio

# Start MinIO
minio server ~/minio-data --console-address ":9001"
```

Access MinIO console at http://localhost:9001 (default credentials: minioadmin/minioadmin)

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

## Usage

1. **Upload Images**: Navigate to the Upload page and drag-and-drop or select images
2. **View People**: Go to the People page to see all detected person groups
3. **View Images**: Browse all uploaded images on the Images page
4. **Person Details**: Click on a person card to see all photos containing that person

## API Endpoints

- `POST /api/upload` - Upload images
- `GET /api/images` - List all images
- `GET /api/images/{id}` - Get image details
- `GET /api/images/{id}/faces` - Get faces in an image
- `GET /api/groups` - List all person groups
- `GET /api/groups/{id}` - Get group details
- `GET /api/groups/{id}/images` - Get images for a person group
- `POST /api/process/{image_id}` - Trigger processing
- `GET /api/processing/status` - Get processing status

## Configuration

Edit `backend/.env` to configure:

- Database connection
- MinIO/S3 credentials
- Face similarity threshold (default: 0.6)
- CORS origins

## Development

### Running Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend Build

```bash
cd frontend
npm run build
```

## Troubleshooting

1. **InsightFace model download**: InsightFace will automatically download models on first use
2. **pgvector extension**: Ensure PostgreSQL has the pgvector extension installed
3. **MinIO bucket**: The application will create the bucket automatically if it doesn't exist
4. **CORS errors**: Make sure `CORS_ORIGINS` in `.env` includes your frontend URL

## License

MIT
