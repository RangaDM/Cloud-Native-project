FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY inventory-service/ ./inventory-service/

# Expose port
EXPOSE 8002

# Run the service
CMD ["python", "inventory-service/main.py"] 