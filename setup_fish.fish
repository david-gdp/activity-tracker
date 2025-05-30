#!/usr/bin/env fish
# Fish shell setup script for ActivityWatch Time Tracker

# Colors for output
set RED '\033[0;31m'
set GREEN '\033[0;32m'
set YELLOW '\033[1;33m'
set NC '\033[0m' # No Color

echo -e "$GREEN""Setting up ActivityWatch Time Tracker for Fish shell...$NC"

# Get the directory where this script is located
set SCRIPT_DIR (dirname (realpath (status --current-filename)))

# Create ~/.local/bin if it doesn't exist
mkdir -p ~/.local/bin

# Copy the script to ~/.local/bin and make it executable
cp "$SCRIPT_DIR/activity_tracker.py" ~/.local/bin/activity-tracker
chmod +x ~/.local/bin/activity-tracker

echo -e "$GREEN""✅ Script installed to ~/.local/bin/activity-tracker$NC"

# Check if ~/.local/bin is in PATH
if contains ~/.local/bin $PATH
    echo -e "$GREEN""✅ ~/.local/bin is already in your PATH$NC"
else
    echo -e "$YELLOW""⚠️  Adding ~/.local/bin to your PATH...$NC"
    
    # Add to Fish config
    if test -f ~/.config/fish/config.fish
        echo -e "$YELLOW""   Adding PATH export to ~/.config/fish/config.fish$NC"
        echo "" >> ~/.config/fish/config.fish
        echo "# Added by ActivityWatch Time Tracker setup" >> ~/.config/fish/config.fish
        echo "set -gx PATH \$PATH ~/.local/bin" >> ~/.config/fish/config.fish
    else
        echo -e "$YELLOW""   Creating ~/.config/fish/config.fish$NC"
        mkdir -p ~/.config/fish
        echo "# Added by ActivityWatch Time Tracker setup" > ~/.config/fish/config.fish
        echo "set -gx PATH \$PATH ~/.local/bin" >> ~/.config/fish/config.fish
    end
    
    # Update PATH for current session
    set -gx PATH $PATH ~/.local/bin
    echo -e "$GREEN""✅ PATH updated for current and future sessions$NC"
end

# Install Python dependencies
echo -e "$GREEN""Installing Python dependencies...$NC"
if command -v pip3 >/dev/null 2>&1
    pip3 install --user -r "$SCRIPT_DIR/requirements.txt"
else if command -v pip >/dev/null 2>&1
    pip install --user -r "$SCRIPT_DIR/requirements.txt"
else
    echo -e "$RED""❌ pip not found. Please install Python pip first.$NC"
    exit 1
end

echo -e "$GREEN""✅ Dependencies installed$NC"

# Test the installation
echo -e "$GREEN""Testing installation...$NC"
if command -v activity-tracker >/dev/null 2>&1
    echo -e "$GREEN""✅ Installation successful!$NC"
    echo -e "$GREEN""   You can now run: activity-tracker --help$NC"
else
    echo -e "$YELLOW""⚠️  Command not found in current session.$NC"
    echo -e "$YELLOW""   Please restart your terminal or run: source ~/.config/fish/config.fish$NC"
    echo -e "$YELLOW""   Then you can run: activity-tracker --help$NC"
end

echo -e "$GREEN""Setup complete! 🎉$NC"
