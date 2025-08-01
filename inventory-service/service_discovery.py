import os
import json
import httpx
import time
from typing import Dict, Optional
from urllib.parse import urlparse

class ServiceDiscovery:
    """
    Service Discovery class that reads service configurations from a GitHub repository file
    and provides dynamic service URLs for inter-service communication.
    """
    
    def __init__(self, github_repo_url: str, service_name: str, service_ip: str):
        """
        Initialize service discovery
        
        Args:
            github_repo_url: GitHub repository URL containing service configuration file
            service_name: Name of the current service (e.g., 'order-service')
            service_ip: IP address of the current service
        """
        self.github_repo_url = github_repo_url
        self.service_name = service_name
        self.service_ip = service_ip
        self.service_configs = {}
        self.last_update = 0
        self.update_interval = 300  # Update every 5 minutes
        
    def _get_raw_github_url(self, file_path: str = "service_config.json") -> str:
        """
        Convert GitHub repository URL to raw file URL
        
        Args:
            file_path: Path to the configuration file in the repository
            
        Returns:
            Raw GitHub file URL
        """
        # Convert github.com URLs to raw.githubusercontent.com
        if "github.com" in self.github_repo_url:
            raw_url = self.github_repo_url.replace("github.com", "raw.githubusercontent.com")
            if not raw_url.endswith("/"):
                raw_url += "/"
            raw_url += "main/" + file_path
            return raw_url
        else:
            # Assume it's already a raw URL
            return self.github_repo_url
    
    def _fetch_service_configs(self) -> Dict[str, str]:
        """
        Fetch service configurations from GitHub repository
        
        Returns:
            Dictionary mapping service names to their IP addresses
        """
        try:
            raw_url = self._get_raw_github_url()
            print(f"🔍 Fetching service configs from: {raw_url}")
            
            async def fetch():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(raw_url)
                    if response.status_code == 200:
                        config_data = response.json()
                        print(f"✅ Successfully fetched service configs: {config_data}")
                        return config_data
                    else:
                        print(f"❌ Failed to fetch service configs. Status: {response.status_code}")
                        return {}
            
            # For synchronous usage, we'll use a simple approach
            import requests
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                config_data = response.json()
                print(f"✅ Successfully fetched service configs: {config_data}")
                return config_data
            else:
                print(f"❌ Failed to fetch service configs. Status: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error fetching service configs: {e}")
            return {}
    
    def _update_service_configs(self):
        """
        Update service configurations if enough time has passed
        """
        current_time = time.time()
        if current_time - self.last_update > self.update_interval:
            print("🔄 Updating service configurations...")
            new_configs = self._fetch_service_configs()
            
            # Only update if we got valid configs from GitHub
            if new_configs:
                self.service_configs = new_configs
                self.last_update = current_time
                
                # Register current service
                if self.service_name not in self.service_configs:
                    self.service_configs[self.service_name] = self.service_ip
                    print(f"📝 Registered current service: {self.service_name} -> {self.service_ip}")
            else:
                # If GitHub fetch failed, keep existing configs and just register current service
                if self.service_name not in self.service_configs:
                    self.service_configs[self.service_name] = self.service_ip
                    print(f"📝 Registered current service: {self.service_name} -> {self.service_ip}")
    
    def get_service_url(self, service_name: str, port: int = None) -> Optional[str]:
        """
        Get the URL for a specific service
        
        Args:
            service_name: Name of the service to get URL for
            port: Port number (if not specified, will use default based on service)
            
        Returns:
            Service URL or None if service not found
        """
        self._update_service_configs()
        
        if service_name not in self.service_configs:
            print(f"⚠️ Service '{service_name}' not found in configuration")
            return None
        
        service_ip = self.service_configs[service_name]
        
        # Use default ports if not specified
        if port is None:
            default_ports = {
                "order-service": 8001,
                "inventory-service": 8002,
                "notification-service": 8003,
                "frontend": 8080
            }
            port = default_ports.get(service_name, 8000)
        
        service_url = f"http://{service_ip}:{port}"
        print(f"🔗 Service URL for {service_name}: {service_url}")
        return service_url
    
    def get_all_service_urls(self) -> Dict[str, str]:
        """
        Get URLs for all known services
        
        Returns:
            Dictionary mapping service names to their URLs
        """
        self._update_service_configs()
        
        service_urls = {}
        for service_name in self.service_configs:
            service_urls[service_name] = self.get_service_url(service_name)
        
        return service_urls
    
    def register_service(self, service_name: str, service_ip: str):
        """
        Register a new service or update existing service
        
        Args:
            service_name: Name of the service
            service_ip: IP address of the service
        """
        self.service_configs[service_name] = service_ip
        print(f"📝 Registered service: {service_name} -> {service_ip}")
    
    def get_current_service_info(self) -> Dict[str, str]:
        """
        Get information about the current service
        
        Returns:
            Dictionary with current service information
        """
        return {
            "service_name": self.service_name,
            "service_ip": self.service_ip,
            "github_repo_url": self.github_repo_url
        }

# Global service discovery instance
_service_discovery = None

def initialize_service_discovery(github_repo_url: str, service_name: str, service_ip: str):
    """
    Initialize the global service discovery instance
    
    Args:
        github_repo_url: GitHub repository URL containing service configuration
        service_name: Name of the current service
        service_ip: IP address of the current service
    """
    global _service_discovery
    _service_discovery = ServiceDiscovery(github_repo_url, service_name, service_ip)
    print(f"🚀 Service discovery initialized for {service_name} at {service_ip}")

def get_service_url(service_name: str, port: int = None) -> Optional[str]:
    """
    Get service URL using the global service discovery instance
    
    Args:
        service_name: Name of the service to get URL for
        port: Port number (optional)
        
    Returns:
        Service URL or None if service not found
    """
    if _service_discovery is None:
        raise RuntimeError("Service discovery not initialized. Call initialize_service_discovery() first.")
    
    return _service_discovery.get_service_url(service_name, port)

def get_all_service_urls() -> Dict[str, str]:
    """
    Get all service URLs using the global service discovery instance
    
    Returns:
        Dictionary mapping service names to their URLs
    """
    if _service_discovery is None:
        raise RuntimeError("Service discovery not initialized. Call initialize_service_discovery() first.")
    
    return _service_discovery.get_all_service_urls() 