from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
import re
import threading
from openai import OpenAI
import time
import json
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, timedelta
import os
from threading import Lock
import pytz
import schedule
import sys
import logging
from logging import handlers
import signal
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

HEADLESS_MODE = True
WAIT_TIMEOUT = 10
MAX_THREADS = 5
THREAD_TIMEOUT = 300
OUTPUT_FILE = "congress_trades.json"
RUNNING = True  # Global flag for graceful shutdown

# Setup logging with rotation
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = logging.handlers.RotatingFileHandler(
    'trades_analyzer.log',
    maxBytes=10_000_000,  # 10MB
    backupCount=5
)
log_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(console_handler)

# Create a lock for thread-safe file writing
file_lock = Lock()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global RUNNING
    logger.info("Shutdown signal received. Waiting for current tasks to complete...")
    RUNNING = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_current_time_est() -> datetime:
    """Get current time in EST/EDT."""
    est = pytz.timezone('America/New_York')
    return datetime.now(est)

def get_timestamp_str() -> str:
    """Get formatted timestamp string."""
    current_time = get_current_time_est()
    return current_time.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")

def initialize_json_file() -> None:
    """Initialize JSON file if it doesn't exist."""
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            json.dump({
                "trading_sessions": []
            }, f, indent=2)

def write_to_json_file(data: Dict[str, Any]) -> None:
    """Write data to JSON file in a thread-safe manner."""
    with file_lock:
        try:
            # Read existing data
            with open(OUTPUT_FILE, 'r') as f:
                file_data = json.load(f)

            # Find or create today's trading session
            current_time = get_current_time_est()
            session_date = current_time.strftime("%Y-%m-%d")
            
            # Look for existing session for today
            session_found = False
            for session in file_data["trading_sessions"]:
                if session["date"] == session_date:
                    session["analyses"].append(data)
                    session_found = True
                    break
            
            # Create new session if none exists for today
            if not session_found:
                new_session = {
                    "date": session_date,
                    "market_open_time": get_timestamp_str(),
                    "analyses": [data]
                }
                file_data["trading_sessions"].append(new_session)
            
            # Write updated data back to file
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(file_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error writing to JSON file: {str(e)}")
            logger.error(traceback.format_exc())

def check_login_status(driver) -> bool:
    """Check if currently logged into Twitter."""
    try:
        # Look for elements that only appear when logged out
        logout_indicators = driver.find_elements(By.CSS_SELECTOR, '[data-testid="loginButton"], [data-testid="signupButton"]')
        return len(logout_indicators) == 0
    except Exception as e:
        logger.error(f"Error checking login status: {str(e)}")
        return False

def login_to_twitter(driver) -> bool:
    """Attempt to log in to Twitter using credentials from environment variables."""
    try:
        TWITTER_EMAIL = os.getenv('TWITTER_USERNAME')
        TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
        
        if not TWITTER_EMAIL or not TWITTER_PASSWORD:
            raise ValueError("Twitter credentials not found in environment variables")
            
        # Navigate to login page
        driver.get("https://twitter.com/i/flow/login")
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        # Enter email
        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[autocomplete="username"]')
        ))
        email_input.send_keys(TWITTER_EMAIL)
        email_input.send_keys(Keys.RETURN)
        
        # Enter password
        password_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[name="password"]')
        ))
        password_input.send_keys(TWITTER_PASSWORD)
        password_input.send_keys(Keys.RETURN)
        
        # Wait for home timeline to load
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="primaryColumn"]')
        ))
        
        # Verify login success
        return check_login_status(driver)
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False
def scroll_to_load_tweets(driver, max_scrolls=5):
    """Scroll the page to load more tweets."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    tweets_found = False
    scrolls = 0
    
    while not tweets_found and scrolls < max_scrolls:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for content to load
        
        # Calculate new scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Try to find tweets
        articles = driver.find_elements(By.TAG_NAME, 'article')
        if articles:
            tweets_found = True
            break
            
        # Break if no more scrolling is possible
        if new_height == last_height:
            break
            
        last_height = new_height
        scrolls += 1
    
    return tweets_found
def get_congress_member_tweets(username: str) -> List[tuple]:
    """Fetch tweets for a given congressional member."""
    options = webdriver.FirefoxOptions()
    if HEADLESS_MODE:
        options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    tweets = []
    
    try:

        # First check login status
        if not check_login_status(driver):
            logger.info("Not logged in. Attempting to log in...")
            login_success = login_to_twitter(driver)
            if not login_success:
                logger.error("Failed to log in to Twitter")
                return []

        driver.get(f"https://twitter.com/{username}")
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
                
        # Wait for the timeline to be present
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="primaryColumn"]')))
        except TimeoutException:
            logger.error(f"Timeline not found for {username}")
            return []
        
        # Scroll and wait for tweets to load
        if not scroll_to_load_tweets(driver):
            logger.error(f"No tweets found for {username} after scrolling")
            return []
        
        # Now get all loaded tweets
        tweet_elements = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'div')
        ))
        logger.info(f"Found {len(tweet_elements)} tweets for {username}")
        #FIGURE OUT WTF IS GOING ON
        for tweet in tweet_elements:
            # Add this inside the loop before trying to find the text
            print(f"Article HTML: {tweet.get_attribute('outerHTML')[:200]}")
            try:
                tweet_text = tweet.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
                tweets.append((username, tweet_text))
            except NoSuchElementException:
                continue
                
        return tweets
    except (NoSuchElementException, TimeoutException) as e:
        logger.error(f"Error fetching tweets for {username}: {str(e)}")
        logger.error(traceback.format_exc())
        return []
    finally:
        driver.quit()

def analyze_tweet(username: str, text: str) -> Optional[Dict[str, Union[str, int]]]:
    """
    Analyze tweet content using GPT to extract trading information.
    Returns structured data about congressional trades.
    """
    if not text:
        return None
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": """
                You are an expert financial analyst with deep expertise in congressional stock trading patterns and market sentiment analysis. Your task is to analyze tweets about congressional trading activity with high precision.

                Key trading indicators to watch for:
                - BULLISH signals: buy, purchase, acquire, long, call options, bought, accumulated, increased position
                - BEARISH signals: sell, sold, dump, short, put options, decreased position, divested, liquidated
                
                Additional context clues:
                - Look for dollar signs ($) followed by stock symbols
                - Watch for position sizing language ("large stake", "small position", etc.)
                - Note timing words ("just", "recently", "today") which indicate trade freshness
                - Consider mentions of options expiry dates or strike prices
                
                Trading magnitude scale guide:
                10: Major position change (>$1M or >50% portfolio shift)
                8-9: Large significant trade
                6-7: Moderate position adjustment
                4-5: Small to medium trade
                1-3: Minor position tweaking

                For each tweet, extract:
                - Name of congressional member (from context or username)
                - Company traded (stock symbol with $ prefix)
                - Trade direction: 
                    'good' = bullish/buying activity
                    'bad' = bearish/selling activity
                - Trade magnitude (1-10 scale based on position size and conviction signals)

                Respond in JSON format with these exact fields:
                {
                    "member_name": string,
                    "company_traded": string,
                    "trade_direction": string (must be exactly "good" or "bad"),
                    "trade_magnitude": integer (1-10),
                    "tweet_text": string
                }

                Only output valid JSON. Return null if no clear trading activity is detected.
                Focus on high-confidence classifications only.
                """
            }, {
                "role": "user",
                "content": f"Analyze this tweet from {username}: {text}"
            }],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        if result:
            result['tweet_text'] = text
            result['timestamp'] = get_timestamp_str()
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing tweet: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def process_tweet(username: str, text: str) -> None:
    """Process a single tweet and write the analysis results to JSON file."""
    if not text:
        return
        
    stock_symbols = re.findall(r'\$([A-Z]+)', text)
    
    if not stock_symbols:
        return
    
    analysis = analyze_tweet(username, text)
    
    if analysis:
        write_to_json_file(analysis)
        logger.info(f"Processed tweet from {username}: {text[:100]}...")

def run_analysis() -> None:
    """Main analysis function that runs at market open."""
    try:
        logger.info(f"Starting analysis at {get_timestamp_str()}")
        
        # Read Twitter handles
        with open("twitter_handles.txt", "r") as f:
            twitter_handles = [line.strip() for line in f.readlines() if line.strip()]
        
        if not twitter_handles:
            raise ValueError("No Twitter handles found in file")
        
        def process_tweets(handles: List[str]) -> None:
            for handle in handles:
                try:
                    tweets = get_congress_member_tweets(handle)
                    for username, tweet in tweets:
                        process_tweet(username, tweet)
                except Exception as e:
                    logger.error(f"Error processing handle {handle}: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
        
        # Split handles among threads
        num_threads = min(MAX_THREADS, len(twitter_handles))
        handles_per_thread = len(twitter_handles) // num_threads
        thread_handles = [
            twitter_handles[i:i + handles_per_thread]
            for i in range(0, len(twitter_handles), handles_per_thread)
        ]
        
        # Start threads
        threads = []
        for handle_group in thread_handles:
            thread = threading.Thread(target=process_tweets, args=(handle_group,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # Wait for threads to complete
        for thread in threads:
            thread.join(timeout=THREAD_TIMEOUT)
            
        logger.info(f"Analysis complete at {get_timestamp_str()}")
            
    except Exception as e:
        logger.error(f"Fatal error in analysis: {str(e)}")
        logger.error(traceback.format_exc())

def restart_program():
    """Restart the entire program."""
    logger.info("Restarting program...")
    try:
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        logger.error(f"Failed to restart: {str(e)}")
        sys.exit(1)

def schedule_market_open() -> None:
    """Schedule the script to run at market open (9:30 AM EST) and keep running indefinitely."""
    global RUNNING
    
    # Initialize JSON file
    initialize_json_file()
    
    # TEST MODE: Uncomment the following line to run analysis immediately without waiting for market open
    run_analysis(); return  # TEST MODE
    
    # Schedule daily runs at 9:30 AM EST
    """schedule.every().monday.at("09:30").do(run_analysis)
    schedule.every().tuesday.at("09:30").do(run_analysis)
    schedule.every().wednesday.at("09:30").do(run_analysis)
    schedule.every().thursday.at("09:30").do(run_analysis)
    schedule.every().friday.at("09:30").do(run_analysis)"""
    
    # Add a heartbeat log every hour to show the script is still running
    schedule.every().hour.do(lambda: logger.info("Scheduler heartbeat - still running"))
    
    logger.info(f"Scheduler initialized at {get_timestamp_str()}")
    logger.info("Waiting for next market open. Will run automatically at 9:30 AM EST on weekdays.")
    
    consecutive_errors = 0
    
    while RUNNING:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            consecutive_errors = 0  # Reset error count on successful iteration
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in main loop: {str(e)}")
            logger.error(traceback.format_exc())
            
            if consecutive_errors >= 5:
                logger.critical("Too many consecutive errors. Attempting restart...")
                restart_program()
            
            # Wait before retrying
            time.sleep(60)

def create_daemon():
    """Run the program as a daemon process."""
    try:
        # Create a new session ID for the daemon process
        if os.name != 'nt':  # Not on Windows
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit first parent
                
            os.setsid()
            
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit second parent
            
            # Close file descriptors
            for fd in range(0, 3):
                try:
                    os.close(fd)
                except OSError:
                    pass
                    
            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            
            with open(os.devnull, 'r') as f:
                os.dup2(f.fileno(), sys.stdin.fileno())
            with open('stdout.log', 'a+') as f:
                os.dup2(f.fileno(), sys.stdout.fileno())
            with open('stderr.log', 'a+') as f:
                os.dup2(f.fileno(), sys.stderr.fileno())
    
    except Exception as e:
        logger.error(f"Failed to daemonize: {str(e)}")
        logger.error(traceback.format_exc())
        return False
        
    return True

if __name__ == "__main__":
    try:
        # Run as daemon on Unix-like systems
        if os.name != 'nt':
            if not create_daemon():
                logger.error("Failed to create daemon. Running in foreground.")
        
        logger.info("Starting Congressional Trade Analyzer...")
        logger.info(f"Process ID: {os.getpid()}")
        logger.info(f"Started at: {get_timestamp_str()}")
        
        # Start the scheduler
        schedule_market_open()
        
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
