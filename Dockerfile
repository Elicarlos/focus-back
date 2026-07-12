FROM python:3.10-slim

WORKDIR /app

# Instala pacotes necessários para compilar psycopg2 (caso necessário) e bibliotecas de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Executa as migrações automáticas do alembic antes de iniciar o servidor uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
