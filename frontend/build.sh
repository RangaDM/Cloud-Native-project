#!/bin/bash

# Frontend Docker build script

echo "🏗️  Building frontend Docker image..."

# Build the frontend image
docker build -t microservices-frontend .

echo "✅ Frontend image built successfully!"
echo "🚀 To run the frontend:"
echo "   docker run -p 8080:8080 microservices-frontend"
echo ""
echo "🔗 Or use docker-compose:"
echo "   docker-compose up -d frontend" 