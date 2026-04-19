
### **File: `Dockerfile`** (For Deployment)
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mx_interpreter.py .
COPY main.py .
COPY bot.mx .

# Run MX file
CMD ["python", "main.py", "bot.mx"]
