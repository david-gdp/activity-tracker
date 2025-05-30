#!/bin/bash
# Setup script to install activity_tracker globally

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up ActivityWatch Time Tracker...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Create ~/.local/bin if it doesn't exist
mkdir -p ~/.local/bin

# Copy the script to ~/.local/bin and make it executable
cp "$SCRIPT_DIR/activity_tracker.py" ~/.local/bin/activity-tracker
chmod +x ~/.local/bin/activity-tracker

echo -e "${GREEN}✅ Script installed to ~/.local/bin/activity-tracker${NC}"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    echo -e "${GREEN}✅ ~/.local/bin is already in your PATH${NC}"
else
    echo -e "${YELLOW}⚠️  ~/.local/bin is not in your PATH${NC}"
    echo -e "${YELLOW}   Please add the following line to your shell configuration:${NC}"
    
    # Detect shell and provide appropriate instructions
    if [[ $SHELL == *"fish"* ]]; then
        echo -e "${YELLOW}   For Fish shell, add to ~/.config/fish/config.fish:${NC}"
        echo -e "${YELLOW}   set -gx PATH \$PATH ~/.local/bin${NC}"
    elif [[ $SHELL == *"zsh"* ]]; then
        echo -e "${YELLOW}   For Zsh, add to ~/.zshrc:${NC}"
        echo -e "${YELLOW}   export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    else
        echo -e "${YELLOW}   For Bash, add to ~/.bashrc:${NC}"
        echo -e "${YELLOW}   export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    fi
    
    echo -e "${YELLOW}   Then restart your terminal or run: source ~/.bashrc (or equivalent)${NC}"
fi

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
if command -v pip3 &> /dev/null; then
    pip3 install --user -r "$SCRIPT_DIR/requirements.txt"
elif command -v pip &> /dev/null; then
    pip install --user -r "$SCRIPT_DIR/requirements.txt"
else
    echo -e "${RED}❌ pip not found. Please install Python pip first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Test the installation
echo -e "${GREEN}Testing installation...${NC}"
if command -v activity-tracker &> /dev/null; then
    echo -e "${GREEN}✅ Installation successful!${NC}"
    echo -e "${GREEN}   You can now run: activity-tracker --help${NC}"
else
    echo -e "${YELLOW}⚠️  Command not found in current session.${NC}"
    echo -e "${YELLOW}   Please restart your terminal or update your PATH as shown above.${NC}"
    echo -e "${YELLOW}   Then you can run: activity-tracker --help${NC}"
fi

echo -e "${GREEN}Setup complete! 🎉${NC}"
