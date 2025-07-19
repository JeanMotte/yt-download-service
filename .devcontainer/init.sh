#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Navigate to the workspace directory.
cd /app/workspace

echo "🚀 Starting development environment setup..."

# Install all project dependencies defined in pyproject.toml
echo "📦 Installing project dependencies..."
poetry install

# Install pre-commit hooks for code quality
echo "🛡️ Installing pre-commit hooks..."
poetry run pre-commit install -f --hook-type pre-commit
poetry run pre-commit autoupdate

# All done!
echo "✅###### READY TO ROCK! ######"