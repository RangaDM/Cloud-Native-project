import os
import json
import threading
import time
from datetime import datetime
from typing import List, Dict, Any

import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import service discovery
from service_discovery import initialize_service_discovery, get_service_url

# Initialize FastAPI app
app = FastAPI(title="Notification Service", version="1.0.0")

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
SERVICE_NAME = os.getenv("SERVICE_NAME", "notification-service")
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
        # Try to get Redis URL from service discovery
        redis_url = get_service_url("redis", 6379)
        if redis_url:
            # Convert HTTP URL to Redis URL format
            redis_url = redis_url.replace("http://", "redis://")
            return redis_url
    except Exception as e:
        print(f"⚠️ Failed to get Redis URL from service discovery: {e}")
    
    # Fallback to environment variable
    return os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.Redis.from_url(
    get_redis_url(),
    decode_responses=True
)

# In-memory storage for notifications (in production, use a database)
notifications_db = []

# Pydantic models
class Notification(BaseModel):
    notification_id: str
    type: str
    message: str
    recipient: str
    timestamp: datetime
    status: str

class TestNotificationRequest(BaseModel):
    message: str
    recipient: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "notification-service"}

@app.get("/notifications")
async def get_notifications():
    """Get all notifications"""
    return {"notifications": notifications_db}

@app.post("/notifications/test")
async def send_test_notification(request: TestNotificationRequest):
    """Send a test notification"""
    notification = create_notification(
        notification_type="test",
        message=request.message,
        recipient=request.recipient
    )
    notifications_db.append(notification.dict())
    return notification

def create_notification(notification_type: str, message: str, recipient: str) -> Notification:
    """Helper function to create a notification"""
    import uuid
    return Notification(
        notification_id=str(uuid.uuid4()),
        type=notification_type,
        message=message,
        recipient=recipient,
        timestamp=datetime.now(),
        status="sent"
    )

def process_notification(notification_data: Dict[str, Any]):
    """
    Process incoming notifications from Redis queue
    This function runs in a separate thread to handle async messages
    """
    try:
        notification_type = notification_data.get("type")
        
        if notification_type == "order_confirmation":
            # Process order confirmation notification
            order_id = notification_data.get("order_id")
            user_id = notification_data.get("user_id")
            total_amount = notification_data.get("total_amount")
            
            message = f"Order {order_id} confirmed! Total: ${total_amount:.2f}"
            notification = create_notification(
                notification_type="order_confirmation",
                message=message,
                recipient=user_id
            )
            
            notifications_db.append(notification.dict())
            print(f"📧 ASYNC: Order confirmation sent to {user_id}: {message}")
            
        elif notification_type == "low_stock_alert":
            # Process low stock alert
            product_id = notification_data.get("product_id")
            product_name = notification_data.get("product_name")
            current_stock = notification_data.get("current_stock")
            
            message = f"Low stock alert: {product_name} ({product_id}) - Only {current_stock} units remaining"
            notification = create_notification(
                notification_type="low_stock_alert",
                message=message,
                recipient="admin@company.com"
            )
            
            notifications_db.append(notification.dict())
            print(f"⚠️ ASYNC: Low stock alert sent: {message}")
            
        elif notification_type == "out_of_stock_alert":
            # Process out of stock alert
            product_id = notification_data.get("product_id")
            product_name = notification_data.get("product_name")
            
            message = f"Out of stock alert: {product_name} ({product_id}) - No units remaining"
            notification = create_notification(
                notification_type="out_of_stock_alert",
                message=message,
                recipient="admin@company.com"
            )
            
            notifications_db.append(notification.dict())
            print(f"🚨 ASYNC: Out of stock alert sent: {message}")
            
        else:
            print(f"❓ ASYNC: Unknown notification type: {notification_type}")
            
    except Exception as e:
        print(f"❌ ASYNC: Error processing notification: {e}")

def redis_listener():
    """
    Background thread that listens to Redis notifications channel
    This demonstrates asynchronous message processing
    """
    pubsub = redis_client.pubsub()
    pubsub.subscribe("notifications")
    
    print("🎧 ASYNC: Notification service listening to Redis queue...")
    
    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                notification_data = json.loads(message["data"])
                print(f"📨 ASYNC: Received notification: {notification_data['type']}")
                
                # Process notification in a separate thread to avoid blocking
                thread = threading.Thread(
                    target=process_notification,
                    args=(notification_data,)
                )
                thread.start()
                
            except json.JSONDecodeError as e:
                print(f"❌ ASYNC: Invalid JSON in notification: {e}")
            except Exception as e:
                print(f"❌ ASYNC: Error processing notification: {e}")

@app.on_event("startup")
async def startup_event():
    """Start the Redis listener thread when the service starts"""
    print("🚀 Starting Notification Service...")
    thread = threading.Thread(target=redis_listener, daemon=True)
    thread.start()
    print("✅ Notification Service started successfully!")

@app.get("/notifications/stats")
async def get_notification_stats():
    """Get notification statistics"""
    total_notifications = len(notifications_db)
    
    # Count by type
    type_counts = {}
    for notification in notifications_db:
        notification_type = notification["type"]
        type_counts[notification_type] = type_counts.get(notification_type, 0) + 1
    
    return {
        "total_notifications": total_notifications,
        "notifications_by_type": type_counts,
        "last_notification": notifications_db[-1] if notifications_db else None
    }

@app.get("/notifications/type/{notification_type}")
async def get_notifications_by_type(notification_type: str):
    """Get notifications by type"""
    filtered_notifications = [
        notification for notification in notifications_db
        if notification["type"] == notification_type
    ]
    return {"notifications": filtered_notifications}

@app.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification"""
    for i, notification in enumerate(notifications_db):
        if notification["notification_id"] == notification_id:
            deleted_notification = notifications_db.pop(i)
            return {"message": f"Notification {notification_id} deleted", "notification": deleted_notification}
    
    raise HTTPException(status_code=404, detail="Notification not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 