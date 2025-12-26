#!/bin/bash
#
# FutureElite Deployment Script
# This script helps automate the deployment process
#
# Usage: ./scripts/deploy.sh [server-user@server-ip]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="futureelite"
APP_DIR="/opt/futureelite"
SERVICE_USER="futureelite"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FutureElite Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running locally or on server
if [ -z "$1" ]; then
    echo -e "${YELLOW}Local deployment preparation mode${NC}"
    echo ""
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env from env.example...${NC}"
        cp env.example .env
        echo -e "${RED}⚠️  IMPORTANT: Edit .env and set SECRET_KEY and other required variables!${NC}"
        echo ""
    fi
    
    # Generate SECRET_KEY if not set or too short
    CURRENT_KEY=$(grep "^SECRET_KEY=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
    if [ -z "$CURRENT_KEY" ] || [ ${#CURRENT_KEY} -lt 32 ] || grep -q "your_secret_key_here" .env 2>/dev/null; then
        echo -e "${YELLOW}Generating SECRET_KEY...${NC}"
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if grep -q "^SECRET_KEY=" .env 2>/dev/null; then
                sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
            else
                echo "SECRET_KEY=$SECRET_KEY" >> .env
            fi
        else
            # Linux
            if grep -q "^SECRET_KEY=" .env 2>/dev/null; then
                sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
            else
                echo "SECRET_KEY=$SECRET_KEY" >> .env
            fi
        fi
        echo -e "${GREEN}✅ SECRET_KEY generated and set in .env${NC}"
        echo ""
    fi
    
    # Set FLASK_ENV if not set
    if ! grep -q "^FLASK_ENV=" .env 2>/dev/null; then
        echo -e "${YELLOW}Setting FLASK_ENV=production...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "FLASK_ENV=production" >> .env
        else
            echo "FLASK_ENV=production" >> .env
        fi
        echo -e "${GREEN}✅ FLASK_ENV set to production${NC}"
        echo ""
    fi
    
    # Run preflight check
    echo -e "${YELLOW}Running preflight check...${NC}"
    if [ -f .env ]; then
        # Export only valid environment variables (skip comments and empty lines)
        # Use a safer method that handles special characters
        while IFS= read -r line; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "${line// }" ]] && continue
            # Export if it contains =
            if [[ "$line" =~ = ]]; then
                export "$line" 2>/dev/null || true
            fi
        done < .env
    fi
    python3 scripts/preflight_check.py
    echo ""
    
    # Create deployment package
    echo -e "${YELLOW}Creating deployment package...${NC}"
    DEPLOY_PKG="futureelite-deployment-$(date +%Y%m%d-%H%M%S).tar.gz"
    # Exclude the deployment package itself if it exists
    tar -czf "$DEPLOY_PKG" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='venv' \
        --exclude='.env' \
        --exclude='data/photos/*' \
        --exclude='*.log' \
        --exclude='futureelite-deployment-*.tar.gz' \
        .
    echo -e "${GREEN}✅ Created: $DEPLOY_PKG${NC}"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Transfer $DEPLOY_PKG to your server"
    echo "2. Follow DEPLOYMENT_GUIDE.md for server setup"
    echo ""
    exit 0
fi

# Remote deployment
SERVER="$1"
echo -e "${YELLOW}Deploying to: $SERVER${NC}"
echo ""

# Check if deployment package exists
DEPLOY_PKG=$(ls -t futureelite-deployment-*.tar.gz 2>/dev/null | head -1)
if [ -z "$DEPLOY_PKG" ]; then
    echo -e "${RED}❌ No deployment package found. Run without arguments first.${NC}"
    exit 1
fi

echo -e "${YELLOW}Transferring deployment package...${NC}"
scp "$DEPLOY_PKG" "$SERVER:/tmp/"
echo -e "${GREEN}✅ Package transferred${NC}"
echo ""

echo -e "${YELLOW}Connecting to server...${NC}"
ssh "$SERVER" << EOF
set -e

echo "Extracting deployment package..."
sudo mkdir -p $APP_DIR
sudo tar -xzf /tmp/$(basename $DEPLOY_PKG) -C $APP_DIR --strip-components=0
sudo chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

echo "Setting up virtual environment..."
cd $APP_DIR
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

echo "Setting up data directory..."
sudo -u $SERVICE_USER mkdir -p data/photos
sudo -u $SERVICE_USER chmod 755 data data/photos

echo "Checking .env file..."
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create it from env.example"
    echo "   sudo -u $SERVICE_USER cp env.example .env"
    echo "   sudo -u $SERVICE_USER nano .env"
fi

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Restarting service..."
sudo systemctl restart $APP_NAME || echo "⚠️  Service not running yet. Start with: sudo systemctl start $APP_NAME"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Ensure .env is configured: sudo -u $SERVICE_USER nano $APP_DIR/.env"
echo "2. Start service: sudo systemctl start $APP_NAME"
echo "3. Check status: sudo systemctl status $APP_NAME"
echo "4. Check logs: sudo journalctl -u $APP_NAME -f"
EOF

echo ""
echo -e "${GREEN}✅ Remote deployment complete!${NC}"
echo ""

