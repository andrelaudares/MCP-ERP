# Dockerfile para aplicação principal (app)
FROM python:3.11-slim

# Variáveis de ambiente para evitar prompts e melhorar logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependências do sistema (se necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia o diretório backend para o diretório de trabalho no contêiner
COPY ./backend /app/backend

# Copia o arquivo de requirements do backend e instala as dependências
COPY backend/requirements.txt /app/backend/requirements.txt

# Instala dependências Python
RUN pip install --upgrade pip \
    && pip install -r /app/backend/requirements.txt

# Volumes para desenvolvimento (serão montados pelo docker-compose)
VOLUME ["/app/backend/src", "/app/backend/scripts", "/app/backend/tasks", "/app/backend/alembic", "/app/backend/alembic.ini"]

# Expõe a porta que o Uvicorn estará ouvindo
EXPOSE 8000

# Comando para executar a aplicação Uvicorn
# Ajustado para referenciar o módulo corretamente a partir do novo WORKDIR /app
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"] 