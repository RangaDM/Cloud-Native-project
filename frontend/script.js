// Service discovery configuration
const GITHUB_REPO_URL = 'https://github.com/RangaDM/cloud-components-config';
const SERVICE_CONFIG_FILE = 'service_config.json';

// Service URLs - Will be loaded dynamically from GitHub
let SERVICES = {};

// Communication log
let communicationLog = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Load service configurations from GitHub
        await loadServiceConfigurations();
        
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
        setInterval(loadServiceConfigurations, 300000); // Reload configs every 5 minutes
    } catch (error) {
        console.error('❌ Failed to initialize application:', error);
        showResult('order-results', 'error', 'Failed to load service configurations. Please check your GitHub repository.');
    }
}

async function loadServiceConfigurations() {
    try {
        console.log('🔍 Loading service configurations from GitHub...');
        
        // Convert GitHub URL to raw URL
        const rawUrl = GITHUB_REPO_URL.replace('github.com', 'raw.githubusercontent.com') + '/main/' + SERVICE_CONFIG_FILE;
        console.log("🔍 Fetching from URL:", rawUrl);
        
        const response = await fetch(rawUrl);
        if (response.ok) {
            const config = await response.json();
            
            // Update service URLs with discovered IPs
            if (config['order-service']) {
                SERVICES.ORDER = `http://${config['order-service']}:8001`;
                console.log(`✅ Order service URL: ${SERVICES.ORDER}`);
            }
            if (config['inventory-service']) {
                SERVICES.INVENTORY = `http://${config['inventory-service']}:8002`;
                console.log(`✅ Inventory service URL: ${SERVICES.INVENTORY}`);
            }
            if (config['notification-service']) {
                SERVICES.NOTIFICATION = `http://${config['notification-service']}:8003`;
                console.log(`✅ Notification service URL: ${SERVICES.NOTIFICATION}`);
            }
            if (config['redis']) {
                SERVICES.REDIS = `redis://${config['redis']}:6379`;
                console.log(`✅ Redis URL: ${SERVICES.REDIS}`);
            }
            
            console.log('✅ Service configurations loaded successfully');
            logCommunication('sync', 'Frontend', 'Service configurations loaded from GitHub');
        } else {
            console.error('❌ Failed to load service configurations from GitHub');
            logCommunication('error', 'Frontend', 'Failed to load service configurations from GitHub');
            throw new Error('Service configurations not available');
        }
    } catch (error) {
        console.error('❌ Error loading service configurations:', error);
        logCommunication('error', 'Frontend', `Service configuration error: ${error.message}`);
        throw error;
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
        { name: 'Order Service', url: SERVICES.ORDER, element: 'order-status' },
        { name: 'Inventory Service', url: SERVICES.INVENTORY, element: 'inventory-status' },
        { name: 'Notification Service', url: SERVICES.NOTIFICATION, element: 'notification-status' }
    ];

    for (const service of services) {
        try {
            const response = await fetch(`${service.url}/health`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                mode: 'cors'
            });
            const status = response.ok ? 'online' : 'offline';
            updateServiceStatus(service.element, status);
            logCommunication('sync', `${service.name}`, `Health check: ${status}`);
        } catch (error) {
            updateServiceStatus(service.element, 'offline');
            logCommunication('error', `${service.name}`, `Connection failed: ${error.message}`);
        }
    }
}

function updateServiceStatus(elementId, status) {
    const element = document.getElementById(elementId);
    element.textContent = status.toUpperCase();
    element.className = `status ${status}`;
}

async function handleOrderSubmission(event) {
    event.preventDefault();
    
    const form = event.target;
    const customerName = document.getElementById('customer-name').value;
    const customerEmail = document.getElementById('customer-email').value;
    
    // Collect order items
    const orderItems = [];
    const itemElements = document.querySelectorAll('.order-item');
    
    itemElements.forEach(item => {
        const productId = item.querySelector('.product-select').value;
        const quantity = parseInt(item.querySelector('.quantity').value);
        
        if (productId && quantity > 0) {
            orderItems.push({
                product_id: productId,
                quantity: quantity
            });
        }
    });
    
    if (orderItems.length === 0) {
        showResult('order-results', 'error', 'Please add at least one item to the order.');
        return;
    }
    
    const orderData = {
        user_id: customerName,  // Using customer name as user_id
        items: orderItems
    };
    
    try {
        logCommunication('sync', 'Order Service', 'Processing order request...');
        console.log('Sending order data:', orderData); // Debug log
        
        const response = await fetch(`${SERVICES.ORDER}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            mode: 'cors',
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showResult('order-results', 'success', `Order created successfully! Order ID: ${result.order_id}`);
            logCommunication('sync', 'Order Service', 'Order processed successfully');
            logCommunication('async', 'Notification Service', 'Order confirmation sent');
            
            // Refresh inventory and notifications
            await loadInventory();
            await loadNotifications();
        } else {
            const errorMessage = result.detail || result.message || 'Unknown error occurred';
            showResult('order-results', 'error', `Error: ${errorMessage}`);
            logCommunication('error', 'Order Service', `Order creation failed: ${errorMessage}`);
        }
    } catch (error) {
        showResult('order-results', 'error', `Network error: ${error.message}`);
        logCommunication('error', 'Order Service', `Network error: ${error.message}`);
    }
}

async function loadProductsForOrder() {
    try {
        const response = await fetch(`${SERVICES.INVENTORY}/products`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        const data = await response.json();
        const products = data.products || data;
        
        // Store products globally for use in order form
        window.availableProducts = products;
        
        // Update existing product selects
        updateProductSelects();
        
    } catch (error) {
        console.error('Failed to load products for order form:', error);
    }
}

function updateProductSelects() {
    const productSelects = document.querySelectorAll('.product-select');
    productSelects.forEach(select => {
        // Clear existing options
        select.innerHTML = '';
        
        // Add options from loaded products
        if (window.availableProducts) {
            window.availableProducts.forEach(product => {
                const option = document.createElement('option');
                option.value = product.product_id;
                option.textContent = `${product.name} ($${product.price})`;
                select.appendChild(option);
            });
        }
    });
}

function addOrderItem() {
    const orderItemsContainer = document.getElementById('order-items');
    const newItem = document.createElement('div');
    newItem.className = 'order-item';
    
    // Create product select with current products
    let productOptions = '';
    if (window.availableProducts) {
        window.availableProducts.forEach(product => {
            productOptions += `<option value="${product.product_id}">${product.name} ($${product.price})</option>`;
        });
    } else {
        // Fallback options if products not loaded yet
        productOptions = `
            <option value="prod001">Laptop ($999.99)</option>
            <option value="prod002">Mouse ($29.99)</option>
            <option value="prod003">Keyboard ($79.99)</option>
            <option value="prod004">NoteBook ($15.00)</option>
        `;
    }
    
    newItem.innerHTML = `
        <select class="product-select">
            ${productOptions}
        </select>
        <input type="number" class="quantity" value="1" min="1" max="10">
        <button type="button" class="remove-item" onclick="removeOrderItem(this)">
            <i class="fas fa-trash"></i>
        </button>
    `;
    orderItemsContainer.appendChild(newItem);
}

function removeOrderItem(button) {
    const orderItemsContainer = document.getElementById('order-items');
    const items = orderItemsContainer.querySelectorAll('.order-item');
    
    if (items.length > 1) {
        button.closest('.order-item').remove();
    }
}

async function loadInventory() {
    try {
        const response = await fetch(`${SERVICES.INVENTORY}/products`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        const data = await response.json();
        
        // Handle the response format: {"products": [...]} or direct array
        const products = data.products || data;
        
        const inventoryGrid = document.getElementById('inventory-grid');
        inventoryGrid.innerHTML = '';
        
        products.forEach(product => {
            const stockClass = product.stock <= 5 ? 'low' : '';
            const item = document.createElement('div');
            item.className = 'inventory-item';
            item.innerHTML = `
                <h4>${product.name}</h4>
                <div class="price">$${product.price}</div>
                <div class="stock ${stockClass}">Stock: ${product.stock}</div>
            `;
            inventoryGrid.appendChild(item);
        });
        
        logCommunication('sync', 'Inventory Service', 'Inventory data loaded');
    } catch (error) {
        logCommunication('error', 'Inventory Service', `Failed to load inventory: ${error.message}`);
    }
}

async function loadNotifications() {
    try {
        const response = await fetch(`${SERVICES.NOTIFICATION}/notifications`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        const data = await response.json();
        
        // Handle the response format: {"notifications": [...]}
        const notifications = data.notifications || data;
        
        const notificationsList = document.getElementById('notifications-list');
        notificationsList.innerHTML = '';
        
        notifications.forEach(notification => {
            const item = document.createElement('div');
            item.className = 'notification-item';
            item.innerHTML = `
                <h4>${notification.type}</h4>
                <p>${notification.message}</p>
                <div class="timestamp">${new Date(notification.timestamp).toLocaleString()}</div>
            `;
            notificationsList.appendChild(item);
        });
        
        logCommunication('sync', 'Notification Service', 'Notifications loaded');
    } catch (error) {
        logCommunication('error', 'Notification Service', `Failed to load notifications: ${error.message}`);
    }
}

async function refreshInventory() {
    await loadInventory();
    showResult('inventory-results', 'info', 'Inventory refreshed successfully');
}

async function testLowStock() {
    try {
        const response = await fetch(`${SERVICES.INVENTORY}/test-low-stock`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        
        if (response.ok) {
            showResult('inventory-results', 'info', 'Low stock alert triggered successfully');
            logCommunication('async', 'Inventory Service', 'Low stock alert sent');
            
            // Refresh notifications to see the new alert
            setTimeout(loadNotifications, 1000);
        } else {
            showResult('inventory-results', 'error', 'Failed to trigger low stock alert');
        }
    } catch (error) {
        showResult('inventory-results', 'error', `Error: ${error.message}`);
    }
}

async function refreshNotifications() {
    await loadNotifications();
    showResult('notification-results', 'info', 'Notifications refreshed successfully');
}

async function clearNotifications() {
    try {
        const response = await fetch(`${SERVICES.NOTIFICATION}/notifications`, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        
        if (response.ok) {
            await loadNotifications();
            showResult('notification-results', 'info', 'All notifications cleared successfully');
            logCommunication('sync', 'Notification Service', 'All notifications cleared');
        } else {
            showResult('notification-results', 'error', 'Failed to clear notifications');
        }
    } catch (error) {
        showResult('notification-results', 'error', `Error: ${error.message}`);
    }
}

function showResult(elementId, type, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `results ${type}`;
    element.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

function logCommunication(type, service, message) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
        timestamp,
        type,
        service,
        message
    };
    
    communicationLog.push(logEntry);
    updateCommunicationLog();
}

function updateCommunicationLog() {
    const logContent = document.getElementById('communication-log');
    logContent.innerHTML = '';
    
    // Show last 20 entries
    const recentEntries = communicationLog.slice(-20);
    
    recentEntries.forEach(entry => {
        const logElement = document.createElement('div');
        logElement.className = `log-entry ${entry.type}`;
        logElement.innerHTML = `
            <div class="log-timestamp">[${entry.timestamp}] ${entry.service}</div>
            <div class="log-message">${entry.message}</div>
        `;
        logContent.appendChild(logElement);
    });
    
    // Auto-scroll to bottom
    logContent.scrollTop = logContent.scrollHeight;
}

function clearLog() {
    communicationLog = [];
    updateCommunicationLog();
}

function exportLog() {
    const logData = communicationLog.map(entry => 
        `[${entry.timestamp}] ${entry.service}: ${entry.message}`
    ).join('\n');
    
    const blob = new Blob([logData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `microservices-log-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Global functions for onclick handlers
window.addOrderItem = addOrderItem;
window.removeOrderItem = removeOrderItem;
window.refreshInventory = refreshInventory;
window.testLowStock = testLowStock;
window.refreshNotifications = refreshNotifications;
window.clearNotifications = clearNotifications;
window.clearLog = clearLog;
window.exportLog = exportLog; 