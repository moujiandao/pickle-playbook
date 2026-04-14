FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY rag/ ./rag/
# /app/backend contains app/, db/, scripts/ etc.
# /app/rag contains the RAG modules.
# Both need to be importable: PYTHONPATH covers both roots.
ENV PYTHONPATH=/app:/app/backend
EXPOSE 8001
WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
