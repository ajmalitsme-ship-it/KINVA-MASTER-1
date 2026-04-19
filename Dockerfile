
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
Copy server.py
# Run server instead of main.py
CMD ["python", "bot.py"]
