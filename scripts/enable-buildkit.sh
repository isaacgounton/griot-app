#!/bin/bash

# Enable Docker BuildKit for faster builds with caching
# This script sets up BuildKit environment variables

echo "🚀 Enabling Docker BuildKit for faster builds..."

# Export BuildKit environment variables
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export BUILDKIT_PROGRESS=plain

# Save to shell profile for persistence (optional)
if [ -f ~/.bashrc ]; then
    if ! grep -q "DOCKER_BUILDKIT=1" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Enable Docker BuildKit" >> ~/.bashrc
        echo "export DOCKER_BUILDKIT=1" >> ~/.bashrc
        echo "export COMPOSE_DOCKER_CLI_BUILD=1" >> ~/.bashrc
        echo "✅ Added BuildKit to ~/.bashrc"
    fi
fi

if [ -f ~/.zshrc ]; then
    if ! grep -q "DOCKER_BUILDKIT=1" ~/.zshrc; then
        echo "" >> ~/.zshrc
        echo "# Enable Docker BuildKit" >> ~/.zshrc
        echo "export DOCKER_BUILDKIT=1" >> ~/.zshrc
        echo "export COMPOSE_DOCKER_CLI_BUILD=1" >> ~/.zshrc
        echo "✅ Added BuildKit to ~/.zshrc"
    fi
fi

echo ""
echo "✅ Docker BuildKit is now enabled!"
echo ""
echo "Your builds will now:"
echo "  - Use layer caching (faster rebuilds)"
echo "  - Cache pip/npm packages"
echo "  - Skip unchanged layers"
echo ""
echo "To build with cache:"
echo "  docker-compose build"
echo ""
echo "To see what changed in your next build:"
echo "  BUILDKIT_PROGRESS=plain docker-compose build"
