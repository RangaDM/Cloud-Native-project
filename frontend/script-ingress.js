// Frontend script for NGINX Ingress deployment
// This version uses the ingress endpoints instead of direct service URLs

// Service URLs - Using Ingress endpoints
const SERVICES = {
    ORDER: '/api/orders',
    INVENTORY: '/api/inventory',
    NOTIFICATION: '/api/notifications',
    FRONTEND: '/'
};

// Communication log
let communicationLog = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        console.log('🚀 Initializing application with Ingress endpoints...');
        
        // Check service health
        await checkServiceHealth();
        
        // Load initial data
        await loadInventory();
        await loadNotifications();
        await loadProductsForOrder(); // Load products for order form
        
        // Set up event listeners
        setupEventListeners();
        
        // Start periodic updates
        setInterval(checkServiceHealth, 30000); // Check every 30 seconds
        setInterval(loadNotifications, 10000); // Refresh notifications every 10 seconds
        
        console.log('✅ Application initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize application:', error);
        showResult('order-results', 'error', 'Failed to initialize application. Please check if all services are running.');
    }
}

function setupEventListeners() {
    // Order form submission
    document.getElementById('order-form').addEventListener('submit', handleOrderSubmission);
    
    // Add order item button
    document.querySelector('[onclick="addOrderItem()"]').addEventListener('click', addOrderItem);
}

async function checkServiceHealth() {
    const services = [
        { name: 'Order Service', url: SERVICES.ORDER + '/health', element: 'order-status' },
        { name: 'Inventory Service', url: SERVICES.INVENTORY + '/health', element: 'inventory-status' },
        { name: 'Notification Service', url: SERVICES.NOTIFICATION + '/health', element: 'notification-status' }
    ];

    for (const service of services) {
        try {
            const response = await fetch(service.url);
            if (response.ok) {
                const data = await response.json();
                updateServiceStatus(service.element, 'online', `${service.name}: ${data.status}`);
                logCommunication('health', service.name, 'Health check successful');
            } else {
                updateServiceStatus(service.element, 'offline', `${service.name}: Unhealthy`);
                logCommunication('error', service.name, `Health check failed: ${response.status}`);
            }
        } catch (error) {
            updateServiceStatus(service.element, 'offline', `${service.name}: Connection failed`);
            logCommunication('error', service.name, `Connection error: ${error.message}`);
        }
    }
}

function updateServiceStatus(elementId, status, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.className = `status ${status}`;
    }
}

async function handleOrderSubmission(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Collect order items
    const items = [];
    const itemRows = document.querySelectorAll('.order-item');
    
    itemRows.forEach(row => {
        const productSelect = row.querySelector('select[name="product_id"]');
        const quantityInput = row.querySelector('input[name="quantity"]');
        
        if (productSelect && quantityInput) {
            items.push({
                product_id: productSelect.value,
                quantity: parseInt(quantityInput.value)
            });
        }
    });
    
    if (items.length === 0) {
        showResult('order-results', 'error', 'Please add at least one item to the order.');
        return;
    }
    
    const orderData = {
        user_id: formData.get('user_id') || 'user123',
        items: items
    };
    
    try {
        console.log('📦 Submitting order:', orderData);
        logCommunication('request', 'Frontend', `Submitting order with ${items.length} items`);
        
        const response = await fetch(SERVICES.ORDER, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Order created successfully:', result);
            showResult('order-results', 'success', `Order created successfully! Order ID: ${result.order_id}`);
            logCommunication('response', 'Order Service', `Order created: ${result.order_id}`);
            
            // Clear the form
            form.reset();
            document.querySelectorAll('.order-item').forEach((item, index) => {
                if (index > 0) item.remove();
            });
            
            // Refresh inventory
            await loadInventory();
        } else {
            const errorData = await response.json();
            console.error('❌ Order creation failed:', errorData);
            showResult('order-results', 'error', `Order creation failed: ${errorData.detail || 'Unknown error'}`);
            logCommunication('error', 'Order Service', `Order creation failed: ${errorData.detail}`);
        }
    } catch (error) {
        console.error('❌ Error submitting order:', error);
        showResult('order-results', 'error', `Network error: ${error.message}`);
        logCommunication('error', 'Frontend', `Network error: ${error.message}`);
    }
}

async function loadProductsForOrder() {
    try {
        const response = await fetch(SERVICES.INVENTORY + '/products');
        if (response.ok) {
            const products = await response.json();
            updateProductSelects(products);
            logCommunication('request', 'Frontend', 'Loaded products for order form');
        } else {
            console.error('❌ Failed to load products for order');
            logCommunication('error', 'Frontend', 'Failed to load products for order form');
        }
    } catch (error) {
        console.error('❌ Error loading products for order:', error);
        logCommunication('error', 'Frontend', `Error loading products: ${error.message}`);
    }
}

function updateProductSelects(products) {
    const selects = document.querySelectorAll('select[name="product_id"]');
    selects.forEach(select => {
        select.innerHTML = '<option value="">Select a product</option>';
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.product_id;
            option.textContent = `${product.name} - $${product.price}`;
            select.appendChild(option);
        });
    });
}

function addOrderItem() {
    const container = document.getElementById('order-items');
    const itemDiv = document.createElement('div');
    itemDiv.className = 'order-item';
    
    // Clone the first order item structure
    const firstItem = container.querySelector('.order-item');
    if (firstItem) {
        itemDiv.innerHTML = firstItem.innerHTML;
        
        // Clear the values
        const select = itemDiv.querySelector('select[name="product_id"]');
        const input = itemDiv.querySelector('input[name="quantity"]');
        if (select) select.value = '';
        if (input) input.value = '1';
        
        // Add remove button
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.textContent = 'Remove';
        removeBtn.onclick = function() { removeOrderItem(this); };
        removeBtn.className = 'remove-btn';
        itemDiv.appendChild(removeBtn);
    }
    
    container.appendChild(itemDiv);
    updateProductSelects(window.products || []);
}

function removeOrderItem(button) {
    button.parentElement.remove();
}

async function loadInventory() {
    try {
        const response = await fetch(SERVICES.INVENTORY + '/products');
        if (response.ok) {
            const products = await response.json();
            window.products = products; // Store for order form
            displayInventory(products);
            logCommunication('request', 'Frontend', 'Loaded inventory data');
        } else {
            console.error('❌ Failed to load inventory');
            logCommunication('error', 'Frontend', 'Failed to load inventory data');
        }
    } catch (error) {
        console.error('❌ Error loading inventory:', error);
        logCommunication('error', 'Frontend', `Error loading inventory: ${error.message}`);
    }
}

function displayInventory(products) {
    const container = document.getElementById('inventory-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    products.forEach(product => {
        const productDiv = document.createElement('div');
        productDiv.className = 'product-item';
        productDiv.innerHTML = `
            <h3>${product.name}</h3>
            <p><strong>ID:</strong> ${product.product_id}</p>
            <p><strong>Price:</strong> $${product.price}</p>
            <p><strong>Stock:</strong> ${product.stock}</p>
            <p><strong>Category:</strong> ${product.category}</p>
        `;
        container.appendChild(productDiv);
    });
}

async function loadNotifications() {
    try {
        const response = await fetch(SERVICES.NOTIFICATION + '/notifications');
        if (response.ok) {
            const notifications = await response.json();
            displayNotifications(notifications);
            logCommunication('request', 'Frontend', 'Loaded notifications');
        } else {
            console.error('❌ Failed to load notifications');
            logCommunication('error', 'Frontend', 'Failed to load notifications');
        }
    } catch (error) {
        console.error('❌ Error loading notifications:', error);
        logCommunication('error', 'Frontend', `Error loading notifications: ${error.message}`);
    }
}

function displayNotifications(notifications) {
    const container = document.getElementById('notifications-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    notifications.forEach(notification => {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'notification-item';
        notificationDiv.innerHTML = `
            <h4>${notification.type}</h4>
            <p><strong>Message:</strong> ${notification.message}</p>
            <p><strong>Recipient:</strong> ${notification.recipient}</p>
            <p><strong>Status:</strong> ${notification.status}</p>
            <p><strong>Time:</strong> ${new Date(notification.timestamp).toLocaleString()}</p>
        `;
        container.appendChild(notificationDiv);
    });
}

// Utility functions
async function refreshInventory() {
    await loadInventory();
}

async function testLowStock() {
    try {
        const response = await fetch(SERVICES.INVENTORY + '/products/prod004/stock');
        if (response.ok) {
            const stock = await response.json();
            if (stock.stock < 5) {
                showResult('inventory-results', 'warning', 'Low stock alert: Notebook has only ' + stock.stock + ' items left!');
            } else {
                showResult('inventory-results', 'info', 'Stock is sufficient: ' + stock.stock + ' items available.');
            }
        }
    } catch (error) {
        showResult('inventory-results', 'error', 'Failed to check stock: ' + error.message);
    }
}

async function refreshNotifications() {
    await loadNotifications();
}

async function clearNotifications() {
    try {
        const response = await fetch(SERVICES.NOTIFICATION + '/notifications', {
            method: 'DELETE'
        });
        if (response.ok) {
            showResult('notification-results', 'success', 'All notifications cleared successfully!');
            await loadNotifications();
            logCommunication('request', 'Frontend', 'Cleared all notifications');
        } else {
            showResult('notification-results', 'error', 'Failed to clear notifications');
        }
    } catch (error) {
        showResult('notification-results', 'error', 'Error clearing notifications: ' + error.message);
    }
}

function showResult(elementId, type, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.className = `result ${type}`;
        element.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

function logCommunication(type, service, message) {
    const timestamp = new Date().toLocaleTimeString();
    communicationLog.push({
        timestamp: timestamp,
        type: type,
        service: service,
        message: message
    });
    
    // Keep only last 50 entries
    if (communicationLog.length > 50) {
        communicationLog = communicationLog.slice(-50);
    }
    
    updateCommunicationLog();
}

function updateCommunicationLog() {
    const container = document.getElementById('communication-log');
    if (!container) return;
    
    container.innerHTML = '';
    
    communicationLog.slice().reverse().forEach(entry => {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${entry.type}`;
        logEntry.innerHTML = `
            <span class="timestamp">${entry.timestamp}</span>
            <span class="service">${entry.service}</span>
            <span class="message">${entry.message}</span>
        `;
        container.appendChild(logEntry);
    });
}

function clearLog() {
    communicationLog = [];
    updateCommunicationLog();
}

function exportLog() {
    const logText = communicationLog.map(entry => 
        `${entry.timestamp} [${entry.type.toUpperCase()}] ${entry.service}: ${entry.message}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'communication-log.txt';
    a.click();
    URL.revokeObjectURL(url);
} 