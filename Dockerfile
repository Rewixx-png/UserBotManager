# file: Dockerfile

# Используем официальный образ Python 3.10 в "slim" версии
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости. --no-cache-dir уменьшает размер образа
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта в рабочую директорию
COPY . .

# Команда для запуска бота при старте контейнера
CMD ["python3", "app.py"]