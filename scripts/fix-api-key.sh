#!/bin/bash

# Script to fix API key authentication issues in Griot
# This script helps sync the API key between frontend and backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Griot - API Key Fix Script ===${NC}\n"

# Function to generate a secure API key
generate_api_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
    else
        echo -e "${RED}❌ .env.example not found. Creating minimal .env${NC}"
        touch .env
    fi
fi

# Check current API_KEY
CURRENT_API_KEY=$(grep -E '^API_KEY=' .env | cut -d '=' -f2 || echo "")

if [ -z "$CURRENT_API_KEY" ] || [ "$CURRENT_API_KEY" = "your_secret_api_key_here" ]; then
    echo -e "${YELLOW}⚠️  No valid API_KEY found in .env${NC}"
    echo -e "${BLUE}🔑 Generating a new secure API key...${NC}"
    
    NEW_API_KEY=$(generate_api_key)
    
    # Update or add API_KEY to .env
    if grep -q '^API_KEY=' .env; then
        # Replace existing API_KEY
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|^API_KEY=.*|API_KEY=$NEW_API_KEY|" .env
        else
            # Linux
            sed -i "s|^API_KEY=.*|API_KEY=$NEW_API_KEY|" .env
        fi
    else
        # Add new API_KEY
        echo "API_KEY=$NEW_API_KEY" >> .env
    fi
    
    echo -e "${GREEN}✅ New API_KEY generated and saved to .env${NC}"
    echo -e "${YELLOW}📝 Your API_KEY is: ${NEW_API_KEY}${NC}"
    echo -e "${YELLOW}⚠️  Please save this key - you'll need it to login!${NC}\n"
    
    API_KEY_TO_USE=$NEW_API_KEY
else
    echo -e "${GREEN}✅ API_KEY already set in .env: ${CURRENT_API_KEY:0:10}...${NC}"
    API_KEY_TO_USE=$CURRENT_API_KEY
fi

# Ask user what they want to do
echo -e "\n${BLUE}What would you like to do?${NC}"
echo "1) Restart backend services (Docker)"
echo "2) Restart backend services (Local)"
echo "3) Show API key for manual frontend login"
echo "4) Exit (I'll handle it manually)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo -e "\n${BLUE}🔄 Restarting Docker services...${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose restart
            echo -e "${GREEN}✅ Docker services restarted${NC}"
        else
            echo -e "${RED}❌ docker-compose not found${NC}"
            exit 1
        fi
        ;;
    2)
        echo -e "\n${YELLOW}⚠️  Please manually restart your backend service${NC}"
        echo -e "   If running with uvicorn, press Ctrl+C and restart"
        ;;
    3)
        echo -e "\n${BLUE}📋 API Key Information:${NC}"
        ;;
    4)
        echo -e "\n${BLUE}👍 Okay, exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

# Display next steps
echo -e "\n${BLUE}=== Next Steps ===${NC}"
echo -e "${GREEN}1.${NC} Open your browser to: ${BLUE}http://localhost:8000${NC}"
echo -e "${GREEN}2.${NC} Go to Login page"
echo -e "${GREEN}3.${NC} Use this API key to login:"
echo -e "   ${YELLOW}${API_KEY_TO_USE}${NC}"
echo -e "${GREEN}4.${NC} Navigate to ${BLUE}/dashboard/chat${NC}"
echo -e "${GREEN}5.${NC} Try a command like: ${YELLOW}/search elon musk${NC}"
echo -e ""
echo -e "${GREEN}✅ If you see search results, authentication is working!${NC}"
echo -e ""

# Option to copy API key to clipboard (if xclip is available)
if command -v xclip &> /dev/null; then
    read -p "Copy API key to clipboard? (y/n): " copy_choice
    if [ "$copy_choice" = "y" ] || [ "$copy_choice" = "Y" ]; then
        echo -n "$API_KEY_TO_USE" | xclip -selection clipboard
        echo -e "${GREEN}✅ API key copied to clipboard!${NC}"
    fi
elif command -v pbcopy &> /dev/null; then
    read -p "Copy API key to clipboard? (y/n): " copy_choice
    if [ "$copy_choice" = "y" ] || [ "$copy_choice" = "Y" ]; then
        echo -n "$API_KEY_TO_USE" | pbcopy
        echo -e "${GREEN}✅ API key copied to clipboard!${NC}"
    fi
fi

echo -e "\n${BLUE}=== Troubleshooting ===${NC}"
echo -e "If you still have issues:"
echo -e "1. Check backend logs: ${YELLOW}docker-compose logs -f backend${NC}"
echo -e "2. Clear browser localStorage: DevTools > Application > Local Storage"
echo -e "3. Read full guide: ${YELLOW}TROUBLESHOOTING_API_KEY.md${NC}"
echo ""
