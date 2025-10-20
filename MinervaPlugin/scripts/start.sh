#!/bin/bash

# Name of the virtual environment directory
VENV_DIR="venv"

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found, creating one..."
    # Create a virtual environment
    python3 -m venv $VENV_DIR
    echo "Virtual environment created."
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Check if RabbitMQ Docker container is running
# if [ ! "$(docker ps -q -f name=rabbitmq)" ]; then
#     echo "RabbitMQ container not running, starting it..."
#     docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4.0-management &
#     echo "RabbitMQ container started."

#     sleep 5
# else
#     echo "RabbitMQ container is already running."
# fi

# Install required packages
pip install -r requirements.txt

python simulator.py

# Deactivate the virtual environment after the script finishes
deactivate