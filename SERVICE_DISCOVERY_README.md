# Dynamic Service Discovery for Microservices

This project implements a dynamic service discovery mechanism that allows microservices to communicate with each other across different VMs by reading service configurations from a GitHub repository.

## 🎯 Overview

Instead of hardcoding service URLs, each service dynamically discovers other services' IP addresses by reading from a centralized configuration file stored in a GitHub repository. This approach enables:

- **Flexible Deployment**: Deploy services on any VM without code changes
- **Dynamic Discovery**: Services automatically find each other's current IP addresses
- **Centralized Configuration**: Single source of truth for service locations
- **Fault Tolerance**: Fallback to environment variables if GitHub is unavailable

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VM 1          │    │   VM 2          │    │   VM 3          │
│                 │    │                 │    │                 │
│ Order Service   │    │ Inventory       │    │ Notification    │
│ (192.168.1.100) │    │ Service         │    │ Service         │
│                 │    │ (192.168.1.101) │    │ (192.168.1.102) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   GitHub Repo   │
                    │                 │
                    │ service_config  │
                    │ .json           │
                    └─────────────────┘
```

## 📋 Prerequisites

1. **GitHub Repository**: Create a repository to store service configurations
2. **Docker**: Installed on all VMs
3. **Network Access**: VMs must be able to reach each other and GitHub

## 🚀 Setup Instructions

### Step 1: Create GitHub Repository Configuration

1. Create a GitHub repository (e.g., `my-microservices-config`)
2. Add a file called `service_config.json` with the following content:

```json
{
  "order-service": "192.168.1.100",
  "inventory-service": "192.168.1.101", 
  "notification-service": "192.168.1.102",
  "frontend": "192.168.1.103",
  "redis": "192.168.1.104"
}
```

**Important**: Replace the IP addresses with the actual IP addresses of your VMs.

### Step 2: Deploy Services on Different VMs

#### On VM 1 (Order Service):
```bash
# Clone your project
git clone <your-project-repo>
cd <your-project-directory>

# Deploy order service
python deploy_service.py order-service \
  --github-repo https://github.com/yourusername/my-microservices-config \
  --redis-ip 192.168.1.104
```

#### On VM 2 (Inventory Service):
```bash
# Clone your project
git clone <your-project-repo>
cd <your-project-directory>

# Deploy inventory service
python deploy_service.py inventory-service \
  --github-repo https://github.com/yourusername/my-microservices-config \
  --redis-ip 192.168.1.104
```

#### On VM 3 (Notification Service):
```bash
# Clone your project
git clone <your-project-repo>
cd <your-project-directory>

# Deploy notification service
python deploy_service.py notification-service \
  --github-repo https://github.com/yourusername/my-microservices-config \
  --redis-ip 192.168.1.104
```

#### On VM 4 (Frontend):
```bash
# Clone your project
git clone <your-project-repo>
cd <your-project-directory>

# Deploy frontend
python deploy_service.py frontend \
  --github-repo https://github.com/yourusername/my-microservices-config
```

### Step 3: Update Service Configuration

When you need to change service IP addresses:

1. Update the `service_config.json` file in your GitHub repository
2. Services will automatically pick up the new configuration within 5 minutes
3. Or restart services to get immediate updates

## 🔧 How It Works

### Service Discovery Module

The `service_discovery.py` module provides:

- **Dynamic URL Resolution**: Converts service names to URLs using current IP addresses
- **GitHub Integration**: Fetches service configurations from GitHub repository
- **Caching**: Updates configurations every 5 minutes to reduce API calls
- **Fallback Support**: Uses environment variables if GitHub is unavailable

### Key Functions

```python
# Initialize service discovery
initialize_service_discovery(github_repo_url, service_name, service_ip)

# Get service URL dynamically
inventory_url = get_service_url("inventory-service", 8002)

# Get all service URLs
all_urls = get_all_service_urls()
```

### Environment Variables

Each service container receives these environment variables:

- `GITHUB_REPO_URL`: GitHub repository containing service config
- `SERVICE_NAME`: Name of the current service
- `SERVICE_IP`: IP address of the current service
- `REDIS_URL`: Redis service URL (if applicable)

## 📊 Monitoring and Debugging

### Check Service Status

```bash
# Check if service is running
docker ps | grep order-service

# View service logs
docker logs order-service

# Check service health
curl http://192.168.1.100:8001/health
```

### Debug Service Discovery

```bash
# View service discovery logs
docker logs order-service | grep -E "(🔍|✅|❌|⚠️)"

# Check service configuration
curl http://192.168.1.100:8001/health
```

## 🔄 Updating Service Configurations

### Method 1: Update GitHub Repository

1. Edit `service_config.json` in your GitHub repository
2. Commit and push changes
3. Services will automatically pick up changes within 5 minutes

### Method 2: Restart Services

```bash
# Restart a service to get immediate configuration updates
docker restart order-service
```

## 🛡️ Security Considerations

1. **GitHub Access**: Ensure all VMs can access your GitHub repository
2. **Network Security**: Configure firewalls to allow inter-service communication
3. **Authentication**: Consider using GitHub tokens for private repositories
4. **HTTPS**: Use HTTPS URLs for GitHub repository access

## 🔧 Troubleshooting

### Common Issues

1. **Service Discovery Fails**
   - Check GitHub repository URL is correct
   - Verify network connectivity to GitHub
   - Check service logs for detailed error messages

2. **Services Can't Communicate**
   - Verify IP addresses in `service_config.json` are correct
   - Check firewall rules between VMs
   - Ensure ports are properly exposed

3. **Docker Build Fails**
   - Check Docker is installed and running
   - Verify all required files are present
   - Check internet connectivity for pulling base images

### Debug Commands

```bash
# Check service discovery initialization
docker logs <service-name> | grep "Service discovery"

# Test GitHub repository access
curl -I https://raw.githubusercontent.com/yourusername/my-microservices-config/main/service_config.json

# Check service connectivity
curl http://<service-ip>:<port>/health
```

## 📝 Example Deployment Script

Create a deployment script for your specific environment:

```bash
#!/bin/bash
# deploy_all_services.sh

GITHUB_REPO="https://github.com/yourusername/my-microservices-config"
REDIS_IP="192.168.1.104"

# Deploy order service
python deploy_service.py order-service --github-repo $GITHUB_REPO --redis-ip $REDIS_IP

# Deploy inventory service  
python deploy_service.py inventory-service --github-repo $GITHUB_REPO --redis-ip $REDIS_IP

# Deploy notification service
python deploy_service.py notification-service --github-repo $GITHUB_REPO --redis-ip $REDIS_IP

# Deploy frontend
python deploy_service.py frontend --github-repo $GITHUB_REPO
```

## 🎉 Benefits

- **Scalability**: Easy to add new services and VMs
- **Flexibility**: Services can be moved between VMs without code changes
- **Reliability**: Fallback mechanisms ensure service availability
- **Maintainability**: Centralized configuration management
- **Cost-Effective**: No need for expensive service discovery solutions

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Documentation](https://redis.io/documentation)

---

**Note**: This implementation provides a lightweight service discovery solution suitable for small to medium-scale deployments. For production environments with high availability requirements, consider using dedicated service discovery solutions like Consul, etcd, or Kubernetes. 