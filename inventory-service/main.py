import os
import json
from datetime import datetime
from typing import List, Dict, Any

import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import service discovery
from service_discovery import initialize_service_discovery, get_service_url

# Initialize FastAPI app
app = FastAPI(title="Inventory Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service discovery initialization
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "https://github.com/RangaDM/cloud-components-config")
SERVICE_NAME = os.getenv("SERVICE_NAME", "inventory-service")
SERVICE_IP = os.getenv("SERVICE_IP", "localhost")

# Initialize service discovery
try:
    initialize_service_discovery(GITHUB_REPO_URL, SERVICE_NAME, SERVICE_IP)
    print(f"✅ Service discovery initialized for {SERVICE_NAME}")
except Exception as e:
    print(f"⚠️ Failed to initialize service discovery: {e}")

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

# In-memory storage for products (in production, use a database)
products_db = {
    "prod001": {
        "product_id": "prod001",
        "name": "Laptop",
        "price": 999.99,
        "stock": 50,
        "category": "Electronics"
    },
    "prod002": {
        "product_id": "prod002",
        "name": "Mouse",
        "price": 29.99,
        "stock": 100,
        "category": "Electronics"
    },
    "prod003": {
        "product_id": "prod003",
        "name": "Keyboard",
        "price": 79.99,
        "stock": 75,
        "category": "Electronics"
    },
    "prod004": {
        "product_id": "prod004",
        "name": "NoteBook",
        "price": 15,
        "stock": 1,
        "category": "Books"
    }
}

# Pydantic models
class Product(BaseModel):
    product_id: str
    name: str
    price: float
    stock: int
    category: str

class UpdateStockRequest(BaseModel):
    quantity: int

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "inventory-service"}

@app.get("/products")
async def get_products():
    """Get all products"""
    return {"products": list(products_db.values())}

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get product by ID"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.put("/products/{product_id}/stock")
async def update_stock(product_id: str, update_request: UpdateStockRequest):
    """
    Update product stock
    Demonstrates synchronous communication (called by Order Service)
    and asynchronous communication (sends low stock alerts)
    """
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    new_stock = product["stock"] + update_request.quantity
    
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Update stock
    product["stock"] = new_stock
    products_db[product_id] = product
    
    print(f"📦 Updated stock for {product_id}: {product['stock']} units")
    
    # Asynchronous communication - Check for low stock alerts
    if new_stock <= 10 and new_stock > 0:
        print("⚠️ ASYNC: Sending low stock alert...")
        alert_message = {
            "type": "low_stock_alert",
            "product_id": product_id,
            "product_name": product["name"],
            "current_stock": new_stock,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Publish to Redis queue for async processing
            redis_client.publish("notifications", json.dumps(alert_message))
            print("✅ ASYNC: Low stock alert queued")
        except Exception as e:
            print(f"⚠️ ASYNC: Failed to queue low stock alert: {e}")
    
    # Asynchronous communication - Out of stock alert
    elif new_stock == 0:
        print("🚨 ASYNC: Sending out of stock alert...")
        alert_message = {
            "type": "out_of_stock_alert",
            "product_id": product_id,
            "product_name": product["name"],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Publish to Redis queue for async processing
            redis_client.publish("notifications", json.dumps(alert_message))
            print("✅ ASYNC: Out of stock alert queued")
        except Exception as e:
            print(f"⚠️ ASYNC: Failed to queue out of stock alert: {e}")
    
    return {
        "product_id": product_id,
        "previous_stock": product["stock"] - update_request.quantity,
        "new_stock": product["stock"],
        "updated_at": datetime.now().isoformat()
    }

@app.post("/products")
async def create_product(product: Product):
    """Create a new product"""
    if product.product_id in products_db:
        raise HTTPException(status_code=400, detail="Product already exists")
    
    products_db[product.product_id] = product.dict()
    return product

@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete a product"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    deleted_product = products_db.pop(product_id)
    return {"message": f"Product {product_id} deleted", "product": deleted_product}

@app.get("/products/{product_id}/stock")
async def get_product_stock(product_id: str):
    """Get product stock level"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "stock": product["stock"],
        "last_updated": datetime.now().isoformat()
    }

@app.get("/products/category/{category}")
async def get_products_by_category(category: str):
    """Get products by category"""
    filtered_products = [
        product for product in products_db.values() 
        if product["category"].lower() == category.lower()
    ]
    return {"products": filtered_products}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 