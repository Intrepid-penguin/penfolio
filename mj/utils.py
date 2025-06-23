import time
from django.conf import settings
import pandas as pd
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import  TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.GEMINI_API_KEY)

USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
]
def scrape_nitter(username='Lf_tobs', max_scrolls=10, proxy=None):
  """
  Scrapes original tweets from a specific user's Nitter profile, skipping retweets and replies.

  Args:
    username (str): The Nitter/Twitter username to scrape.
    max_scrolls (int): The maximum number of times to scroll down.
    proxy (str, optional): Proxy server to use (e.g., "ip:port"). Defaults to None.
  
  Returns:
    pandas.DataFrame: A DataFrame containing the scraped tweet data.
  """
  
  print("Setting up the WebDriver...")
  service = Service(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  
  user_agent = random.choice(USER_AGENTS)
  options.add_argument(f'user-agent={user_agent}')
  print(f"Using User-Agent: {user_agent}")

  if proxy:
    options.add_argument(f'--proxy-server={proxy}')
    print(f"Using proxy: {proxy}")

  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')

  options.add_argument("window-size=1920,1080")
  options.add_argument("--disable-blink-features=AutomationControlled")
  
  driver = webdriver.Chrome(service=service, options=options)

  driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

  url = f"https://nitter.net/{username}"
  print(f"Navigating to: {url}")
  driver.get(url)

  # Check if user exists
  if "User not found" in driver.page_source or "This account doesn't exist" in driver.page_source or driver.title == "404":
    print(f"User '{username}' not found or account doesn't exist.")
    driver.quit()
    return pd.DataFrame()

  if "Guest account rate limit exceeded" in driver.page_source or "Too many requests" in driver.page_source:
    print("Rate limit exceeded on initial page load. Try again later or use a different IP/proxy.")
    driver.quit()
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
    driver.quit()
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
      
  print(f"Scraping complete. Found {len(scraped_data)} original tweets. Closing WebDriver.")
  driver.quit()
  
  return pd.DataFrame(scraped_data)

def get_twitter_inspo(username: str, scrolls: int = 10, proxy: str = None):
  SCROLLS = 10
  PROXY = None
  existing_cache = user_exists_in_cache(username)
  cache_dir = ".cache"
  
  if existing_cache:
    print(f"User '{username}' data already exists in cache. Loading from cache...")
    
    cache_file = os.path.join(cache_dir, f"{username}.json")
    return pd.read_json(cache_file, orient="records").to_json()
  
  tweet_df = scrape_nitter(username, SCROLLS, proxy=PROXY)
  
  if not tweet_df.empty:
    print("\n--- Scraped Data (First 5 Rows as JSON) ---")
    print(tweet_df.head().to_json(orient="records", indent=2))
    os.makedirs(cache_dir, exist_ok=True)
    output_filename = os.path.join(cache_dir, f"{username}.json")
    tweet_df.to_json(output_filename, orient="records", indent=4)
    return tweet_df.to_json()
  
  return None


def user_exists_in_cache(username: str) -> bool:
  """
  Check if a user's data exists in the .cache folder.
  
  Args:
    username (str): The username to check for in cache.
  
  Returns:
    bool: True if user data exists in cache, False otherwise.
  """
  cache_dir = ".cache"
  cache_file = os.path.join(cache_dir, f"{username}.json")
  return os.path.exists(cache_file)



instruction = """
You are an expert social media content generator with a keen eye for subtle stylistic nuances. Your task is to analyze a user's unique tweeting style from a provided JSON dataset of their tweets, and then apply that learned style to convert a separate journal entry into a new tweet.

**Here's the data you will receive:**

1.  **JSON Data of Tweets:** A JSON array containing multiple tweet objects from a single user. You will primarily focus on the `content` field of these tweets.
2.  **Journal Entry:** A piece of text that needs to be rewritten as a tweet in the user's style.

**Your Process:**

1.  **Style Extraction:** First, meticulously go through the `content` of each tweet in the provided JSON. Identify and internalize the distinct patterns and characteristics of the user's tweeting style. Consider:
    *   **Tone:** (e.g., sarcastic, humorous, reflective, casual, formal, observational, complaining, enthusiastic, ironic, witty, direct, understated)
    *   **Typical Tweet Length:** (e.g., very short and punchy, medium length, often approaching character limits, single sentences or multiple short ones)
    *   **Vocabulary & Language Use:** (e.g., uses slang, internet shorthand like "lol" "ikr", simple language, complex words, specific jargon, conversational, formal diction)
    *   **Punctuation & Emojis:** (e.g., frequent use of emojis, specific punctuation habits like ellipses, multiple exclamation marks, minimal punctuation, capitalized words for emphasis)
    *   **Sentence Structure & Flow:** (e.g., short declarative sentences, rhetorical questions, fragmented thoughts, narrative style, stream-of-consciousness, use of parentheticals)
    *   **Use of Hashtags/Mentions:** (e.g., rarely uses, uses relevant hashtags, uses trending hashtags, mentions specific accounts, doesn't use at all, uses ironic hashtags)
    *   **Overall Vibe/Persona:** (e.g., laid-back, energetic, cynical, optimistic, analytical, dramatic)

2.  **Tweet Conversion:** Once you've thoroughly grasped the user's style, take the provided journal entry and convert it into a new tweet that seamlessly integrates all the observed stylistic elements.
    *   **Authenticity:** The new tweet must sound as if the original user wrote it, incorporating their tone, vocabulary, punctuation, and structure.
    *   **Content Preservation:** While adapting the style, ensure the core message or sentiment of the journal entry is accurately and fully retained.
    *   **Conciseness:** The generated tweet should be concise and fit within typical tweet length (ideally under 280 characters, but prioritize the *observed* typical length from the user's past tweets).

**Output Requirement:**

Your response must contain **ONLY** the generated tweet text. Do not include any introductory remarks, style analysis, or additional commentary.
"""


def generate_tweet(json_data: str, journal_entry: str, system_instruction: str = instruction):
  """
  Generate content using Gemini AI with JSON input.
  
  Args:
    json_data (str): JSON string containing the content to process
    system_instruction (str): System instruction for the AI model
  
  Returns:
    str: Generated response text
  """
  prompt = f"""
  Here is the JSON data of a user's tweets: {json_data}
  Here is the journal entry: {journal_entry}
  """
  response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
      system_instruction=system_instruction),
    contents=prompt
  )
  
  return response.text
