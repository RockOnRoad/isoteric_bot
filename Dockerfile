FROM python:3.12.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	gcc \
    build-essential \
    bash \
    procps \
    iputils-ping \
    curl \
    wget \
    nmap \
    htop \
 && rm -rf /var/lib/apt/lists/*

 # Копируем только метаданные сначала (оптимизация кеша)
COPY pyproject.toml uv.lock* ./

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install .

# Запуск приложения
CMD ["python", "-m", "app_v1.main"]