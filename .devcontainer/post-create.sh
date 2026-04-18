#!/bin/bash
set -e

echo "🚀 VorstersNV Development Environment Setup"

# Update system packages
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo "📱 Installing Node.js dependencies..."
cd frontend && npm install && cd ..

# Set up pre-commit hooks (optional)
if command -v pre-commit &> /dev/null; then
    echo "🔗 Setting up pre-commit hooks..."
    pre-commit install
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cat > .env << 'EOF'
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_DEFAULT_MODEL=llama3
WEBHOOK_SECRET=dev-secret-change-me
DB_URL=postgresql+asyncpg://vorstersNV:dev-password-change-me@postgres:5432/vorstersNV
REDIS_URL=redis://redis:6379
EOF
    echo "✅ .env created (update with actual values)"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Available commands:"
echo "  - docker-compose up -d    (start all services)"
echo "  - pytest tests/ -v         (run tests)"
echo "  - python scripts/set_mode.py --mode build"
echo "  - cd frontend && npm run dev  (start Next.js)"
echo ""
