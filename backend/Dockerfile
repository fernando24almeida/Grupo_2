# Dockerfile para o Backend (FastAPI)
FROM python:3.10-slim

# Definir o diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias para o psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar os requisitos e instalar as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação
COPY . .

# Expor a porta que o FastAPI utiliza (o Render detecta esta porta)
EXPOSE 8000

# Comando para iniciar a aplicação usando a porta definida pelo Render (variável PORT)
# Se a variável PORT não estiver definida, usa a 8000 por defeito.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

