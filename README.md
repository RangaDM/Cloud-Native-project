# Microservices Communication Patterns Demo

This project demonstrates both **Synchronous** and **Asynchronous** communication patterns between microservices using a simple e-commerce scenario.

## Architecture Overview

### Services
1. **Order Service** - Handles order creation and management
2. **Inventory Service** - Manages product inventory
3. **Notification Service** - Sends notifications to users

### Communication Patterns

#### Synchronous Communication (HTTP/REST)
- **Order Service** → **Inventory Service**: Check product availability
- **Order Service** → **Inventory Service**: Update inventory after order

#### Asynchronous Communication (Message Queue)
- **Order Service** → **Notification Service**: Send order confirmation emails
- **Inventory Service** → **Notification Service**: Send low stock alerts

## Project Structure

```
microservices-demo/
├── order-service/          # Order management microservice
├── inventory-service/      # Inventory management microservice
├── notification-service/   # Notification microservice
├── docker-compose.yml     # Docker orchestration
├── README.md             # This file
└── requirements.txt       # Python dependencies
```

## Technologies Used

- **Python 3.8+** with FastAPI
- **Redis** for message queue (asynchronous communication)
- **Docker** for containerization
- **Docker Compose** for orchestration

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.8+ (for local development)

### Running with Docker Compose

1. **Clone and navigate to the project:**
```bash
cd microservices-demo
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **Check service status:**
```bash
docker-compose ps
```

4. **View logs:**
```bash
docker-compose logs -f
```

### Running Locally

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start Redis:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

3. **Start services in separate terminals:**
```bash
# Terminal 1
cd order-service && python main.py

# Terminal 2
cd inventory-service && python main.py

# Terminal 3
cd notification-service && python main.py
```

### Frontend Demo

1. **Start all services with Docker Compose (Recommended):**
```bash
docker-compose up -d
# This starts all services including the frontend at http://localhost:8080
```

2. **Or start backend services first, then frontend:**
```bash
# Start backend services
docker-compose up -d redis order-service inventory-service notification-service

# Start frontend
docker-compose up -d frontend
```

3. **For local development:**
```bash
# Start the backend services first (using Docker Compose or local development)

# Then serve the frontend:
cd frontend
python serve_frontend.py
# Or open directly: open frontend/index.html
```

The frontend provides a user-friendly interface to:
- Create orders and see synchronous communication in action
- View inventory and test low stock alerts
- Monitor notifications and asynchronous communication
- Real-time communication log showing all service interactions

## API Endpoints

### Order Service (Port 8001)
- `POST /orders` - Create a new order
- `GET /orders/{order_id}` - Get order details
- `GET /orders` - List all orders

### Inventory Service (Port 8002)
- `GET /products/{product_id}` - Get product details
- `PUT /products/{product_id}/stock` - Update product stock
- `GET /products` - List all products

### Notification Service (Port 8003)
- `GET /notifications` - List all notifications
- `POST /notifications/test` - Send test notification

## Testing the Communication Patterns

### 1. Synchronous Communication Test

Create an order (this will trigger synchronous calls to inventory service):

```bash
curl -X POST "http://localhost:8001/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "items": [
      {
        "product_id": "prod001",
        "quantity": 2
      }
    ]
  }'
```

### 2. Asynchronous Communication Test

The order creation will automatically trigger:
- Order confirmation email (async)
- Inventory update notifications (async)

Check notifications:
```bash
curl "http://localhost:8003/notifications"
```

## Communication Flow

### Order Creation Flow
1. **Client** → **Order Service**: POST /orders
2. **Order Service** → **Inventory Service**: Check stock (SYNC)
3. **Order Service** → **Inventory Service**: Update stock (SYNC)
4. **Order Service** → **Notification Service**: Send confirmation (ASYNC)
5. **Inventory Service** → **Notification Service**: Low stock alert (ASYNC)

## Key Learning Points

### Synchronous Communication
- **Pros**: Immediate response, simple to implement
- **Cons**: Tight coupling, potential for cascading failures
- **Use Cases**: Critical operations requiring immediate validation

### Asynchronous Communication
- **Pros**: Loose coupling, better fault tolerance
- **Cons**: Eventual consistency, more complex debugging
- **Use Cases**: Non-critical operations, background tasks

## Monitoring and Debugging

### View Service Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs order-service
```

### Redis Queue Monitoring
```bash
# Connect to Redis CLI
docker exec -it microservices-demo_redis_1 redis-cli

# Monitor queue
MONITOR
```

### Health Checks
```bash
# Order Service
curl http://localhost:8001/health

# Inventory Service
curl http://localhost:8002/health

# Notification Service
curl http://localhost:8003/health
```

## Cleanup

Stop all services:
```bash
docker-compose down
```

Remove all containers and volumes:
```bash
docker-compose down -v
```

## Next Steps

1. **Add Circuit Breakers** for synchronous communication
2. **Implement Retry Mechanisms** for failed async messages
3. **Add Monitoring** with Prometheus and Grafana
4. **Implement API Gateway** for centralized routing
5. **Add Authentication** and Authorization
6. **Implement Database** per service pattern

## Troubleshooting

### Common Issues

1. **Port already in use**: Change ports in docker-compose.yml
2. **Redis connection failed**: Ensure Redis container is running
3. **Service not responding**: Check logs with `docker-compose logs`

### Debug Mode

Run services in debug mode:
```bash
docker-compose -f docker-compose.debug.yml up
```

This will show detailed logs and enable hot reloading for development. 