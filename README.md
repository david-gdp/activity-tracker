# ActivityWatch Time Tracker

A Python script to fetch data from ActivityWatch and calculate total non-idle and idle time for a day.

## Prerequisites

1. **ActivityWatch must be running** on your system at `localhost:5600`
2. Python 3.6 or higher

## Installation

### Option 1: Global Installation (Recommended)

For Fish shell users:
```bash
./setup_fish.fish
```

For Bash/Zsh users:
```bash
./setup.sh
```

After installation, restart your terminal or run:
```fish
# For Fish shell
source ~/.config/fish/config.fish
```

```bash
# For Bash/Zsh
source ~/.bashrc  # or ~/.zshrc
```

Now you can use `activity-tracker` from anywhere!

### Option 2: Local Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make the script executable (optional):
```bash
chmod +x activity_tracker.py
```

## Usage

### Global Installation
```bash
# Analyze today's data
activity-tracker

# Analyze specific date
activity-tracker --date 2025-05-27

# Custom host/port
activity-tracker --host localhost --port 5600

# Show help
activity-tracker --help
```

### Local Installation
```bash
# Analyze today's data
python activity_tracker.py

# Analyze specific date
python activity_tracker.py --date 2025-05-27
```

## Command Line Options

- `--date YYYY-MM-DD`: Specific date to analyze (default: today)
- `--host HOST`: ActivityWatch host (default: localhost)  
- `--port PORT`: ActivityWatch port (default: 5600)
- `--help`: Show help message

## Output

The script will display:
- Active time (non-idle) in hours and minutes
- Idle time in hours and minutes
- Total tracked time
- Percentage breakdown of active vs idle time

Example output:
```
==================================================
DAILY TIME SUMMARY
==================================================
Active Time:  6.45 hours (387 minutes)
Idle Time:    2.18 hours (131 minutes)
Total Time:   8.63 hours
Active:       74.7%
Idle:         25.3%
==================================================
```

## How It Works

1. Connects to the ActivityWatch API at the specified host/port
2. Retrieves all available data buckets
3. Focuses on AFK (Away From Keyboard) buckets to determine activity status
4. Calculates total time spent in "not-afk" (active) and "afk" (idle) states
5. Displays a summary with hours, minutes, and percentages

## Troubleshooting

- **Connection Error**: Make sure ActivityWatch is running and accessible at the specified host/port
- **No Data**: Ensure ActivityWatch has been collecting data for the specified date
- **No AFK Buckets**: The script relies on AFK watchers to determine idle time. Make sure ActivityWatch AFK watchers are enabled

## Dependencies

- `requests`: For making HTTP API calls to ActivityWatch
