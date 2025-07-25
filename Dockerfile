# Base image (default platform is usually fine unless targeting M1 Mac)
FROM python:3.10-slim

# If you're on Apple M1/M2 and facing issues, then use:
# FROM --platform=linux/amd64 python:3.10-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

# Install system dependencies for PyMuPDF (fitz)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY process_pdfs.py .
COPY pdf_extractor.py .
COPY heading_detector.py .

# Create input/output folders (these will be volume-mounted)
RUN mkdir -p /app/input /app/output

# Set execute permissions (optional, for consistency)
RUN chmod +x process_pdfs.py

# Optional health check to verify fitz (PyMuPDF) is importable
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
 CMD python -c "import fitz; print('Dependencies OK')" || exit 1

# Default command
CMD ["python", "process_pdfs.py"]
