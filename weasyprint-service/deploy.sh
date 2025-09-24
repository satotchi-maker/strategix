#!/bin/bash

# WeasyPrint Service Deployment Script
# This script can be used with Railway, Render, or similar PaaS providers

echo "WeasyPrint Service Deployment"
echo "=============================="

# Configuration for deployment
SERVICE_NAME="weasyprint-pdf-service"
DOCKERFILE_PATH="./Dockerfile"

# Function to deploy to Railway
deploy_railway() {
    echo "Deploying to Railway..."
    
    # Check if Railway CLI is installed
    if ! command -v railway &> /dev/null; then
        echo "Railway CLI not installed. Installing..."
        curl -fsSL https://railway.app/install.sh | sh
    fi
    
    # Initialize Railway project if not exists
    if [ ! -f ".railway.toml" ]; then
        railway login
        railway link
    fi
    
    # Deploy
    railway up -d
    
    # Get the deployment URL
    echo "Getting deployment URL..."
    railway status
    railway domain
}

# Function to deploy to Render
deploy_render() {
    echo "Creating render.yaml for Render deployment..."
    
    cat > render.yaml << EOF
services:
  - type: web
    name: ${SERVICE_NAME}
    env: docker
    dockerfilePath: ${DOCKERFILE_PATH}
    envVars:
      - key: WEASYPRINT_API_KEY
        generateValue: true
      - key: ALLOWED_ORIGINS
        value: "*"
    healthCheckPath: /health
    autoDeploy: false
EOF
    
    echo "render.yaml created. Push to GitHub and connect to Render."
    echo "Visit https://render.com to complete deployment."
}

# Function to deploy using Docker locally
deploy_local() {
    echo "Building and running locally with Docker..."
    docker-compose up --build -d
    echo "Service running at http://localhost:8000"
    echo "API documentation available at http://localhost:8000/docs"
}

# Function to deploy to Fly.io
deploy_fly() {
    echo "Deploying to Fly.io..."
    
    # Check if Fly CLI is installed
    if ! command -v flyctl &> /dev/null; then
        echo "Fly CLI not installed. Installing..."
        curl -L https://fly.io/install.sh | sh
    fi
    
    # Create fly.toml if not exists
    if [ ! -f "fly.toml" ]; then
        flyctl launch --name ${SERVICE_NAME} --no-deploy
    fi
    
    # Set secrets
    flyctl secrets set WEASYPRINT_API_KEY=$(openssl rand -hex 32)
    
    # Deploy
    flyctl deploy
    
    # Get the deployment URL
    flyctl status
    echo "Service deployed to: https://${SERVICE_NAME}.fly.dev"
}

# Main menu
echo ""
echo "Select deployment target:"
echo "1) Railway (Recommended for quick deployment)"
echo "2) Render"
echo "3) Fly.io"
echo "4) Local Docker"
echo "5) Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        deploy_railway
        ;;
    2)
        deploy_render
        ;;
    3)
        deploy_fly
        ;;
    4)
        deploy_local
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "Deployment process completed!"
echo "Remember to save the deployment URL for your Base44 configuration."