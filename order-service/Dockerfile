FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || (echo "Failed to install requirements" && cat requirements.txt && exit 1)

# Copy service code
COPY order-service/ ./order-service/

# Expose port
EXPOSE 8001

# Run the service
CMD ["python", "order-service/main.py"] 