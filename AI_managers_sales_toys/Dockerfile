FROM python:3.11

WORKDIR /app

# Копіюємо та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо всі файли проекту
COPY . .

# Запускаємо застосунок
CMD ["python", "main.py"]