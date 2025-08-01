import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

import redis
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import service discovery
from service_discovery import initialize_service_discovery, get_service_url

# Initialize FastAPI app
app = FastAPI(title="Order Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection for async communication
def get_redis_url():
    """Get Redis URL from service discovery or environment variable"""
    try:
        # Try to get Redis IP from service discovery
        redis_service_url = get_service_url("redis", 6379)
        if redis_service_url:
            # Extract IP from the service URL and create Redis URL
            from urllib.parse import urlparse
            parsed_url = urlparse(redis_service_url)
            redis_ip = parsed_url.hostname
            return f"redis://{redis_ip}:6379"
    except Exception as e:
        print(f"⚠️ Failed to get Redis URL from service discovery: {e}")
    
    # Fallback to environment variable
    return os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.Redis.from_url(
    get_redis_url(),
    decode_responses=True
)

# Service discovery initialization
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "https://github.com/RangaDM/cloud-components-config")
SERVICE_NAME = os.getenv("SERVICE_NAME", "order-service")
SERVICE_IP = os.getenv("SERVICE_IP", "localhost")

# Initialize service discovery
try:
    initialize_service_discovery(GITHUB_REPO_URL, SERVICE_NAME, SERVICE_IP)
    print(f"✅ Service discovery initialized for {SERVICE_NAME}")
except Exception as e:
    print(f"⚠️ Failed to initialize service discovery: {e}")

# Fallback URLs for synchronous communication (used if service discovery fails)
# INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8002")
# NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8003")

# In-memory storage for orders (in production, use a database)
orders_db = {}

# Pydantic models
class OrderItem(BaseModel):
    product_id: str
    quantity: int

class CreateOrderRequest(BaseModel):
    user_id: str
    items: List[OrderItem]

class Order(BaseModel):
    order_id: str
    user_id: str
    items: List[OrderItem]
    status: str
    total_amount: float
    created_at: datetime

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "order-service"}

@app.get("/orders")
async def get_orders():
    """Get all orders"""
    return {"orders": list(orders_db.values())}

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order by ID"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

@app.post("/orders", response_model=Order)
async def create_order(order_request: CreateOrderRequest):
    """
    Create a new order
    Demonstrates both synchronous and asynchronous communication:
    - SYNC: Check inventory and update stock
    - ASYNC: Send order confirmation notification
    """
    order_id = str(uuid.uuid4())
    
    print(f"🛒 Creating order {order_id} for user {order_request.user_id}")
    
    # Step 1: Synchronous communication - Check inventory
    print("📞 SYNC: Checking inventory availability...")
    
    # Get inventory service URL dynamically
    inventory_url = get_service_url("inventory-service", 8002) or INVENTORY_SERVICE_URL
    print(f"🔗 Using inventory service URL: {inventory_url}")
    
    async with httpx.AsyncClient() as client:
        try:
            # Check each product's availability
            for item in order_request.items:
                response = await client.get(
                    f"{inventory_url}/products/{item.product_id}"
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Product {item.product_id} not found"
                    )
                
                product_data = response.json()
                if product_data["stock"] < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for product {item.product_id}"
                    )
            
            print("✅ SYNC: Inventory check successful")
            
            # Step 2: Synchronous communication - Update inventory
            print("📞 SYNC: Updating inventory...")
            for item in order_request.items:
                response = await client.put(
                    f"{inventory_url}/products/{item.product_id}/stock",
                    json={"quantity": -item.quantity}  # Reduce stock
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to update inventory for product {item.product_id}"
                    )
            
            print("✅ SYNC: Inventory updated successfully")
            
            # Step 3: Calculate total amount using real prices from inventory
            print("💰 SYNC: Calculating total amount with real prices...")
            total_amount = 0.0
            for item in order_request.items:
                # Get product details to get the real price
                response = await client.get(f"{inventory_url}/products/{item.product_id}")
                if response.status_code == 200:
                    product_data = response.json()
                    item_total = item.quantity * product_data["price"]
                    total_amount += item_total
                    print(f"💰 Product {item.product_id}: {item.quantity} x ${product_data['price']} = ${item_total}")
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to get price for product {item.product_id}"
                    )
            
            print(f"💰 Total amount: ${total_amount}")
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Inventory service unavailable: {str(e)}")
    
    # Create order object
    order = Order(
        order_id=order_id,
        user_id=order_request.user_id,
        items=order_request.items,
        status="confirmed",
        total_amount=total_amount,
        created_at=datetime.now()
    )
    
    # Store order
    orders_db[order_id] = order.dict()
    
    # Step 4: Asynchronous communication - Send order confirmation
    print("📨 ASYNC: Sending order confirmation notification...")
    notification_message = {
        "type": "order_confirmation",
        "order_id": order_id,
        "user_id": order_request.user_id,
        "total_amount": total_amount,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Publish to Redis queue for async processing
        redis_client.publish("notifications", json.dumps(notification_message))
        print("✅ ASYNC: Order confirmation notification queued")
    except Exception as e:
        print(f"⚠️ ASYNC: Failed to queue notification: {e}")
        # Don't fail the order creation if notification fails
    
    print(f"🎉 Order {order_id} created successfully!")
    return order

@app.get("/orders/{order_id}/status")
async def get_order_status(order_id: str):
    """Get order status"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    return {
        "order_id": order_id,
        "status": order["status"],
        "created_at": order["created_at"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 