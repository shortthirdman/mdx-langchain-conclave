FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY deployment/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY deployment/bakery_server.py .
COPY rag_artifacts/bakery_faiss_index/ ./bakery_faiss_index/
COPY data/ ./data/
COPY .env .

# Expose port
EXPOSE 8000

# Run server, respecting the PORT environment variable for cloud environments
CMD ["sh", "-c", "uvicorn bakery_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
