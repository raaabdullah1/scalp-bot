#!/bin/bash

# ScalpBot Setup Script

echo "🚀 ScalpBot Deployment Setup"
echo "=========================="

echo "Checking Python version..."
python3 --version

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Edit secrets.py file with your credentials"
echo "3. Run the bot with: python final_bot.py"
echo "4. Access the dashboard at http://localhost:8080"

echo ""
echo "For cloud deployment, follow the instructions in DEPLOYMENT_README.md"
