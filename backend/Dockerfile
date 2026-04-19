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

# Expor a porta que o FastAPI utiliza
EXPOSE 8000

# Comando para iniciar a aplicação
# Nota: "app.main:app" assume que estamos no diretório /app (que contém a pasta 'app')
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
