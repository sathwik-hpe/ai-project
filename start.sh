#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🚀 K8s AI Agent - Setup & Start"
echo "=========================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check Kubernetes cluster
echo "🔍 Checking Kubernetes cluster..."
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster is not running or not accessible."
    echo "   Please start your cluster (minikube, kind, Docker Desktop, etc.)"
    exit 1
fi

echo "✅ Kubernetes cluster is running"
kubectl get nodes

echo ""
echo "=========================================="
echo "🔑 Groq API Key Setup"
echo "=========================================="
echo ""
echo "You need a free Groq API key to use this agent."
echo "Get one at: https://console.groq.com"
echo ""

# Check if GROQ_API_KEY is already set
if [ -z "$GROQ_API_KEY" ]; then
    read -p "Enter your Groq API key: " GROQ_API_KEY
    
    if [ -z "$GROQ_API_KEY" ]; then
        echo "❌ API key cannot be empty"
        exit 1
    fi
    
    export GROQ_API_KEY
fi

echo "✅ API key configured"
echo ""

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null || true

# Build and start
echo ""
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check API health
echo "🔍 Checking API service..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API service is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Waiting for API... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ API service failed to start"
    echo "   Check logs with: docker-compose logs api"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ K8s AI Agent is Running!"
echo "=========================================="
echo ""
echo "🌐 Chat UI:  http://localhost:3000"
echo "📡 API:      http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Try asking:"
echo "   - What's wrong in my cluster?"
echo "   - List all pods"
echo "   - Why is my pod crashing?"
echo ""
echo "🛑 To stop:  docker-compose down"
echo "📋 Logs:     docker-compose logs -f"
echo ""

# Open browser (optional)
if command -v open &> /dev/null; then
    echo "🌐 Opening browser..."
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
fi

echo "✨ Ready to go!"
