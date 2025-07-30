#!/bin/bash
# SAGE Setup Script - Creates virtual environment and installs everything

set -e  # Exit on error

echo "🎓 SAGE Setup Script"
echo "==================="
echo

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Remove it? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Using existing virtual environment..."
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install SAGE in development mode
echo "📦 Installing SAGE and dependencies..."
pip install -e ".[dev]"

# Check Ollama
echo
echo "🤖 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is running"
        
        # List available models
        echo
        echo "Available models:"
        curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('models', [])
if models:
    for m in models:
        print(f'  - {m[\"name\"]}')
else:
    print('  No models found')
"
        
        # Check for required models
        echo
        echo "Checking required models..."
        required_models=("llama2:7b" "llama3.2:latest")
        optional_models=("deepseek-r1:latest" "llama2:13b")
        missing_models=()
        
        for model in "${required_models[@]}"; do
            if curl -s http://localhost:11434/api/tags | grep -q "\"$model\""; then
                echo "  ✓ $model"
            else
                echo "  ✗ $model (missing)"
                missing_models+=("$model")
            fi
        done
        
        # Offer to pull missing models
        if [ ${#missing_models[@]} -gt 0 ]; then
            echo
            echo "⚠️  Some required models are missing. Pull them now? (y/N)"
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                for model in "${missing_models[@]}"; do
                    echo "Pulling $model..."
                    ollama pull "$model"
                done
            fi
        fi
        
        # Check optional models
        echo
        echo "Optional models (for enhanced features):"
        for model in "${optional_models[@]}"; do
            if curl -s http://localhost:11434/api/tags | grep -q "\"$model\""; then
                echo "  ✓ $model"
            else
                echo "  ○ $model (not installed)"
            fi
        done
    else
        echo "⚠️  Ollama is not running"
        echo "   Start it with: ollama serve"
    fi
else
    echo "⚠️  Ollama is not installed"
    echo "   Install from: https://ollama.ai"
fi

# Create data directory
echo
echo "📁 Creating data directory..."
mkdir -p ~/.sage/data

# Final instructions
echo
echo "✅ Setup complete!"
echo
echo "To use SAGE:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo
echo "  2. Make sure Ollama is running:"
echo "     ollama serve"
echo
echo "  3. Run SAGE:"
echo "     sage learn"
echo
echo "For testing instructions, see TEST_README.md"