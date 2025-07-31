FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY notification-service/ ./notification-service/

# Expose port
EXPOSE 8003

# Run the service
CMD ["python", "notification-service/main.py"] 