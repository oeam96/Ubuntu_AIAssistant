#!/bin/bash

# Path to the project directory
PROJECT_DIR=~/gnome_assistant

# Path to the virtual environment
VENV_PATH="$PROJECT_DIR/venv"

# Path to the Python script
PYTHON_SCRIPT="$PROJECT_DIR/ai_assistant2.py"

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping Ollama service..."
    sudo systemctl stop ollama.service
    sudo systemctl disable ollama.service
    echo "Deactivating virtual environment..."
    deactivate
    exit
}

# Trap EXIT signal to ensure cleanup is called
trap cleanup EXIT

# Start Ollama service in the background
echo "Starting Ollama service..."
sudo systemctl enable ollama.service
sudo systemctl start ollama.service

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Run the Python script
echo "Running AI Assistant..."
python3 "$PYTHON_SCRIPT"
