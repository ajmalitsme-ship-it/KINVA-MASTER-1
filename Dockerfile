
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mx_interpreter.py .
COPY main.py .
COPY server.py .
COPY bot.tsx .

# Run server instead of main.py
CMD ["python", "server.py"]
