FROM python:3.12-slim

WORKDIR /app

# Установка uv для управления зависимостями
RUN pip install uv

# Копирование файлов зависимостей
COPY pyproject.toml uv.lock ./

# Установка зависимостей
RUN uv pip install --system -r pyproject.toml

# Копирование кода приложения
COPY . .

# Установка переменной окружения для Python
ENV PYTHONPATH=/app

# Запуск приложения
CMD ["python", "-m", "app_v1.main"]