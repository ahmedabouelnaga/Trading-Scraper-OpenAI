# Congressional Trades Analyzer

## ⚠️ Disclaimer and Legal Notice

This tool is created for **EDUCATIONAL PURPOSES ONLY**. It is designed to demonstrate:
- Web scraping techniques
- Natural language processing
- Automated data analysis
- Financial data processing
- System automation

**IMPORTANT NOTICES:**
- This tool is not intended for any illegal activities
- Not intended for actual trading or financial decisions
- No guarantee of accuracy or completeness of data
- Use at your own risk
- Ensure compliance with all applicable laws and regulations
- Respect Twitter's terms of service and API limitations
- Not affiliated with any government entity or official

**LEGAL DISCLAIMER:**
- The authors take no responsibility for any use or misuse of this code
- This code is provided "as is" without warranty of any kind
- Users are solely responsible for how they use this code
- Do NOT use this code for website scraping at rates that could constitute a denial of service attack
- Do NOT attempt to circumvent any website's terms of service or access limits
- This is posted purely as a learning exercise and demonstration
- Always implement appropriate rate limiting and respect robots.txt
- Users must ensure their use complies with all applicable laws and terms of service

**RESPONSIBLE USAGE:**
- Implement reasonable delays between requests
- Respect website rate limits
- Monitor system resource usage
- Do not attempt to overwhelm or degrade services
- Scale operations appropriately

By using this tool, you acknowledge that:
1. You are using it solely for educational and research purposes
2. You take full responsibility for your use of the code
3. You will comply with all applicable laws and terms of service
4. You understand the authors assume no liability for your use of the code

A Python-based automation tool that monitors congressional Twitter accounts for stock trading activity, analyzes the tweets using GPT-3.5, and maintains a structured record of trading patterns.

## Overview

This script automatically:
- Scrapes tweets from specified congressional Twitter accounts
- Analyzes tweets for stock trading activity using GPT-3.5
- Identifies trading direction (bullish/bearish) and magnitude
- Records analyses in a structured JSON format
- Runs automatically at market open (9:30 AM EST) on weekdays
- Operates continuously as a background daemon process

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Firefox browser (required for Selenium)
- Unix-like operating system (for daemon mode) or Windows

### Required Python Packages
```bash
pip install selenium
pip install openai
pip install schedule
pip install pytz
pip install webdriver-manager
```

### API Keys Required
- OpenAI API key (for GPT-3.5 analysis)

## Installation

1. Clone the repository or download the script:
```bash
git clone https://github.com/ahmed/Trade-Scraper-OpenAI.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up the configuration:
   - Replace the `OPENAI_API_KEY` in the script with your API key
   - Create a `twitter_handles.txt` file with Twitter handles to monitor (one per line)

## Testing the Script

### Testing Outside Market Hours
To test the script immediately without waiting for market open:

1. Open `trades_analyzer.py`
2. Find the `schedule_market_open()` function
3. Uncomment the test mode line (around line 380):
```python
# TEST MODE: Uncomment the following line to run analysis immediately without waiting for market open
run_analysis(); return  # TEST MODE
```
4. Save the file and run the script

### Reverting to Normal Operation
After testing, to return to normal market-hours operation:

1. Comment out the test mode line again:
```python
# TEST MODE: Uncomment the following line to run analysis immediately without waiting for market open
# run_analysis(); return  # TEST MODE
```
2. Save the file and restart the script

## Stopping the Script

The script is designed to run continuously, but there are several ways to stop it:

### Method 1: Graceful Shutdown (Recommended)
If running in foreground:
```bash
# Press Ctrl+C
```

If running in background:
```bash
# Find the process ID
ps aux | grep trades_analyzer.py

# Stop gracefully
kill <PID>
```

### Method 2: Force Stop (Use only if Method 1 fails)
```bash
# Find the process ID
ps aux | grep trades_analyzer.py

# Force stop
kill -9 <PID>
```

### Method 3: Using Process ID File
```bash
# Kill using PID file (if running as daemon)
kill $(cat trades_analyzer.pid)
```

### Verifying the Script Has Stopped
```bash
# Check if process is still running
ps aux | grep trades_analyzer.py

# Check the logs for shutdown message
tail trades_analyzer.log
```

## Configuration Files

### twitter_handles.txt
```text
@CongressMember1
@CongressMember2
@CongressMember3
```

### Output Structure (congress_trades.json)
```json
{
  "trading_sessions": [
    {
      "date": "2024-02-09",
      "market_open_time": "Friday, February 09, 2024 09:30:00 AM EST",
      "analyses": [
        {
          "member_name": "string",
          "company_traded": "string",
          "trade_direction": "good/bad",
          "trade_magnitude": "integer (1-10)",
          "tweet_text": "string",
          "timestamp": "string"
        }
      ]
    }
  ]
}
```

## Usage

### Starting the Script
```bash
python trades_analyzer.py
```

The script will:
1. Create necessary log files
2. Start running in the background (daemon mode on Unix systems)
3. Automatically execute at market open (9:30 AM EST) on weekdays
4. Continue running until explicitly stopped

### Monitoring

#### Log Files
- `trades_analyzer.log`: Main application logs
- `stdout.log`: Standard output
- `stderr.log`: Error messages
- `congress_trades.json`: Trading analysis results

To monitor the logs in real-time:
```bash
tail -f trades_analyzer.log
```

### Stopping the Script

1. Find the process ID:
```bash
ps aux | grep trades_analyzer.py
```

2. Stop the script gracefully:
```bash
kill <PID>
```
The script will complete any ongoing analysis before shutting down.

For force stop (not recommended):
```bash
kill -9 <PID>
```

## Error Handling

The script includes robust error handling:
- Automatic restart after 5 consecutive errors
- Rotated log files to prevent disk space issues
- Thread-safe file operations
- Graceful shutdown handling

## Maintenance

### Log Rotation
Logs are automatically rotated:
- Maximum file size: 10MB
- Keeps last 5 log files
- Automatically handles compression

### Debugging
If issues occur:
1. Check the error logs:
```bash
cat stderr.log
```
2. View the main application log:
```bash
cat trades_analyzer.log
```

## Trading Analysis Details

### Trade Direction Classification
- 'good' = bullish/buying activity
- 'bad' = bearish/selling activity

### Magnitude Scale (1-10)
- 10: Major position change (>$1M or >50% portfolio shift)
- 8-9: Large significant trade
- 6-7: Moderate position adjustment
- 4-5: Small to medium trade
- 1-3: Minor position tweaking

## Security Notes

- API keys should be stored securely (consider using environment variables)
- The script runs with user privileges only
- No sensitive data is transmitted outside the local system
- All analysis is logged locally

## Troubleshooting

### Common Issues

1. Selenium WebDriver Issues
```bash
# Update Firefox
sudo apt update && sudo apt upgrade firefox

# Check webdriver
python -c "from selenium import webdriver; print(webdriver.__version__)"
```

2. Permission Issues
```bash
# Ensure proper file permissions
chmod +x trades_analyzer.py
chmod 666 congress_trades.json
```

3. Log File Issues
```bash
# Reset log files
rm *.log
touch trades_analyzer.log stdout.log stderr.log
```

### Getting Help
If you encounter issues:
1. Check the logs for specific error messages
2. Ensure all prerequisites are installed
3. Verify API key validity
4. Check file permissions
5. Contact support with log files if needed