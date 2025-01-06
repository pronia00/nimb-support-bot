FROM python:3.11.8-slim

# Добавляем переменные окружения для вывода логов
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

WORKDIR /app

# Копируем сначала только requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы
COPY . .

# Убираем создание пользователя appuser, так как это может вызывать проблемы с правами доступа к .env
# Убираем EXPOSE 8000, так как нам не нужен порт для телеграм бота

CMD ["python", "-u", "GPTBot.py"]
