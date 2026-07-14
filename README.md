# Sortline

Turn a messy product folder into a clean catalog. Sortline extracts features, drops duplicates, clusters look-alikes, names them from on-image text, and strips the backgrounds — automatically.

## Features
- **Feature Extraction**: Deep learning-based image feature extraction.
- **Deduplication**: Identifies and removes duplicate images.
- **Clustering**: Automatically groups similar or look-alike products together.
- **OCR Naming**: Extracts on-image text to dynamically name clusters and files.
- **Background Removal**: Automatically strips backgrounds from product images.
- **Exporting**: Batch export cleaned and named product photos in a neat catalog structure.

## Tech Stack
- **Frontend**: React, TypeScript, Vite
- **Backend**: FastAPI, Python (PyTorch, OpenCV for ML/vision tasks)
- **Database**: SQLite (SQLAlchemy)

## Getting Started

### Backend Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the FastAPI server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

## Usage
Simply drag and drop a folder containing your raw product shoots into the web interface. Sortline will handle the processing and present you with grouped, named, and background-stripped images for review before final export.
