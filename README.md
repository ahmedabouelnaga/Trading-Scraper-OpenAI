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


# Detailed Code Block Explanation - OpenAI Version

## 1. Imports and Initial Setup
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
# ... other imports ...
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
```
This section:
- Imports all necessary tools and libraries
- Loads secret information (like API keys) from a .env file
- Sets up basic functionality for web scraping and AI analysis

## 2. Configuration and API Setup
```python
# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

HEADLESS_MODE = True
WAIT_TIMEOUT = 10
MAX_THREADS = 5
```
This part:
- Gets the OpenAI API key from environment variables
- Sets up basic settings like:
  * Running Firefox invisibly (HEADLESS_MODE)
  * How long to wait for web pages (WAIT_TIMEOUT)
  * How many parallel processes to run (MAX_THREADS)

## 3. Logging Setup
```python
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = logging.handlers.RotatingFileHandler(
    'trades_analyzer.log',
    maxBytes=10_000_000,  # 10MB
    backupCount=5
)
```
This sets up:
- A system to record all program activities
- Log files that automatically rotate at 10MB
- Keeps last 5 log files for history

## 4. File Management Functions
```python
def initialize_json_file() -> None:
    """Initialize JSON file if it doesn't exist."""
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            json.dump({
                "trading_sessions": []
            }, f, indent=2)

def write_to_json_file(data: Dict[str, Any]) -> None:
    """Write data to JSON file in a thread-safe manner."""
```
These functions:
- Create and manage the output file
- Safely write new trading data
- Organize data by trading sessions
- Handle multiple processes writing at once

## 5. Tweet Collection Function
```python
def get_congress_member_tweets(username: str) -> List[tuple]:
    """Fetch tweets for a given congressional member."""
    options = webdriver.FirefoxOptions()
    if HEADLESS_MODE:
        options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
```
This function:
- Opens Firefox browser (invisibly)
- Goes to a Twitter profile
- Collects all recent tweets
- Handles errors if Twitter doesn't load

## 6. OpenAI Analysis Function
```python
def analyze_tweet(username: str, text: str) -> Optional[Dict[str, Union[str, int]]]:
    """Analyze tweet content using GPT to extract trading information."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": """..."""
            }]
```
This function:
- Takes a tweet
- Sends it to GPT-3.5-turbo
- Uses a detailed prompt to analyze trading information
- Returns structured data about any trades mentioned

## 7. Tweet Processing Function
```python
def process_tweet(username: str, text: str) -> None:
    """Process a single tweet and write the analysis results to JSON file."""
    if not text:
        return
        
    stock_symbols = re.findall(r'\$([A-Z]+)', text)
```
This function:
- Checks tweets for stock symbols ($AAPL format)
- Only analyzes tweets with stock mentions
- Saves analysis results to the JSON file

## 8. Main Analysis Runner
```python
def run_analysis() -> None:
    """Main analysis function that runs at market open."""
    try:
        logger.info(f"Starting analysis at {get_timestamp_str()}")
        
        # Read Twitter handles
        with open("twitter_handles.txt", "r") as f:
            twitter_handles = [line.strip() for line in f.readlines()]
```
This coordinates:
- Reading the list of Twitter accounts
- Starting multiple threads for faster processing
- Managing the overall analysis process

## 9. Scheduling System
```python
def schedule_market_open() -> None:
    """Schedule the script to run at market open (9:30 AM EST)."""
    # Schedule daily runs at 9:30 AM EST
    schedule.every().monday.at("09:30").do(run_analysis)
    schedule.every().tuesday.at("09:30").do(run_analysis)
```
This part:
- Sets up automatic running at market open
- Includes a test mode for immediate running
- Adds hourly checks to ensure it's still running

## 10. Background Process Setup
```python
def create_daemon():
    """Run the program as a daemon process."""
    try:
        if os.name != 'nt':  # Not on Windows
            pid = os.fork()
```
This function:
- Makes the program run in the background
- Sets up proper logging
- Handles different operating systems

## Main Differences from Gemini Version:
1. Uses OpenAI's GPT-3.5-turbo instead of Gemini
2. Slightly different API setup and error handling
3. Similar core functionality but different AI interface
4. Includes full market hours scheduling by default
5. Similar daemon process handling

The workflow remains the same:
1. Start program
2. Load Twitter handles
3. Check for tweets with stock symbols
4. Analyze using GPT-3.5
5. Save results
6. Keep running on schedule
