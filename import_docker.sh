FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    langgraph \
    langchain-openai \
    qdrant-client \
    sqlalchemy \
    psycopg2-binary \
    pydantic \
    python-dotenv \
    httpx \
    sentence-transformers

COPY backend/app /app/app

WORKDIR /app

ENV PYTHONPATH=/app

CMD ["python", "-c", "from app.services.embedding import embedding_service; print('OK')"]
