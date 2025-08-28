import time
import pandas as pd
import random
import tempfile
import shutil
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import  TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
]

def scrape_nitter(username='Lf_tobs', max_scrolls=5, proxy=None):
  """
  Scrapes original tweets from a specific user's Nitter profile, skipping retweets and replies.

  Args:
    username (str): The Nitter/Twitter username to scrape.
    max_scrolls (int): The maximum number of times to scroll down.
    proxy (str, optional): Proxy server to use (e.g., "ip:port"). Defaults to None.
  
  Returns:
    pandas.DataFrame: A DataFrame containing the scraped tweet data.
  """
  # Create unique temporary directory with timestamp and UUID
  unique_id = str(uuid.uuid4())[:8]
  timestamp = str(int(time.time()))
  temp_dir = tempfile.mkdtemp(prefix=f'chrome_profile_{timestamp}_{unique_id}_')
  driver = None
  try:
    print("Setting up the WebDriver...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'user-agent={user_agent}')
    print(f"Using User-Agent: {user_agent}")

    if proxy:
      options.add_argument(f'--proxy-server={proxy}')
      print(f"Using proxy: {proxy}")

    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument(f'--user-data-dir={temp_dir}')
    options.add_argument('--remote-debugging-port=9222')

    options.add_argument('--disable-setuid-sandbox')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    url = f"https://nitter.net/{username}"
    print(f"Navigating to: {url}")
    driver.get(url)

    if "Guest account rate limit exceeded" in driver.page_source or "Too many requests" in driver.page_source:
      print("Rate limit exceeded on initial page load. Try again later or use a different IP/proxy.")
      return pd.DataFrame()

    print(f"Scrolling down to load more tweets (up to {max_scrolls} times)...")
    try:
      WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "timeline-item"))
      )
      
      last_height = driver.execute_script("return document.body.scrollHeight")
      scroll_count = 0
      
      while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(random.uniform(2.5, 5.0))

        try:
          load_more_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".show-more a"))
          )
          print("Found and clicking 'Load more' button.")
          driver.execute_script("arguments[0].click();", load_more_button)
          time.sleep(random.uniform(2.0, 4.0))
        except TimeoutException:
          print("'Load more' button not found, continuing scroll check.")
          pass

        if "Guest account rate limit exceeded" in driver.page_source or "Too many requests" in driver.page_source:
          print("Rate limit hit during scrolling. Stopping scrape.")
          break

        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
          print("Reached the end of the results or no new content loaded.")
          break
        
        last_height = new_height
        scroll_count += 1
        print(f"Scroll #{scroll_count} completed.")

    except TimeoutException:
      print(f"No tweets found for user '{username}' or page took too long to load.")
      return pd.DataFrame()

    print("Scraping tweet data from the page...")
    tweet_elements = driver.find_elements(By.CLASS_NAME, "timeline-item")
    print(f"Found {len(tweet_elements)} timeline items. Filtering for original tweets by @{username}...")
    
    scraped_data = []

    for tweet in tweet_elements:
      try:
        if tweet.find_elements(By.CLASS_NAME, "retweet-header"):
          continue
        
        if tweet.find_elements(By.CLASS_NAME, "replying-to"):
          continue

        handle = tweet.find_element(By.CLASS_NAME, "username").text.strip()
        if handle != f"@{username}":
          continue

        username_scraped = tweet.find_element(By.CLASS_NAME, "fullname").text.strip()
        
        date_element = tweet.find_element(By.CLASS_NAME, "tweet-date").find_element(By.TAG_NAME, "a")
        timestamp = date_element.get_attribute("title")
        permalink = date_element.get_attribute("href")

        content = tweet.find_element(By.CLASS_NAME, "tweet-content").text.strip()
        
        stats_div = tweet.find_element(By.CLASS_NAME, "tweet-stats")
        replies = stats_div.find_element(By.CSS_SELECTOR, ".icon-comment").find_element(By.XPATH, "..").text.strip()
        retweets = stats_div.find_element(By.CSS_SELECTOR, ".icon-retweet").find_element(By.XPATH, "..").text.strip()
        likes = stats_div.find_element(By.CSS_SELECTOR, ".icon-heart").find_element(By.XPATH, "..").text.strip()

        scraped_data.append({
          "username": username_scraped,
          "handle": handle,
          "timestamp": timestamp,
          "content": content,
          "replies": int(replies.replace(',', '')) if replies else 0,
          "retweets": int(retweets.replace(',', '')) if retweets else 0,
          "likes": int(likes.replace(',', '')) if likes else 0,
          "permalink": permalink
        })

      except Exception as e:
        print(f"Could not parse a tweet, skipping. Error: {e}")
        continue
        
    print(f"Scraping complete. Found {len(scraped_data)} original tweets.")
    
    return pd.DataFrame(scraped_data)
  finally:
    if driver:
      print("Closing WebDriver.")
      driver.quit()
    print(f"Cleaning up temporary directory: {temp_dir}")
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
  USERNAME = "seatedro"
  SCROLLS = 10
  PROXY = None
  tweet_df = scrape_nitter(USERNAME, SCROLLS, proxy=PROXY)
  
  if not tweet_df.empty:
    print("\n--- Scraped Data (First 5 Rows as JSON) ---")
    print(tweet_df.head().to_json(orient="records", indent=2))
    
    output_filename = f"nitter_scrape_{USERNAME}.json"
    tweet_df.to_json(output_filename, orient="records", indent=4)
    print(f"\nData successfully saved to {output_filename}")
  else:
    print(f"\nNo original tweets were scraped for user @{USERNAME}.")
