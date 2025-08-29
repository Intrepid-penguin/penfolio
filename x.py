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
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
]

def scrape_x(username="elonmusk", max_scrolls=10, proxy=None):
    """
    Scrapes tweets from a public X.com (Twitter) profile timeline.
    Skips retweets and replies (best-effort, since X.com is JS-heavy).
    """

    unique_id = str(uuid.uuid4())[:8]
    timestamp = str(int(time.time()))
    temp_dir = tempfile.mkdtemp(prefix=f'chrome_profile_{timestamp}_{unique_id}_')
    driver = None
    try:
        print("Setting up the WebDriver...")
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()

        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f"user-agent={user_agent}")
        print(f"Using User-Agent: {user_agent}")

        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
            print(f"Using proxy: {proxy}")

        # Headless + server-safe flags
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--remote-debugging-pipe")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        url = f"https://x.com/{username}"
        print(f"Navigating to: {url}")
        driver.get(url)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//article"))
            )
        except TimeoutException:
            print(f"No tweets found for user '{username}' or page did not load.")
            return pd.DataFrame()

        print(f"Scrolling down to load tweets (up to {max_scrolls} times)...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0

        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2.5, 5.0))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more tweets loaded.")
                break
            last_height = new_height
            scroll_count += 1
            print(f"Scroll #{scroll_count} complete.")

        print("Scraping tweets...")
        tweet_elements = driver.find_elements(By.XPATH, "//article")
        print(f"Found {len(tweet_elements)} tweets on the page.")

        scraped_data = []
        for tweet in tweet_elements:
            try:
                # Grab tweet text
                content = " ".join([e.text for e in tweet.find_elements(By.XPATH, ".//div[@data-testid='tweetText']")]).strip()
                if not content:
                    continue

                # Tweet timestamp + link
                try:
                    date_element = tweet.find_element(By.XPATH, ".//time/..")
                    timestamp = date_element.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                    permalink = date_element.get_attribute("href")
                except:
                    timestamp, permalink = None, None

                # Stats (best-effort)
                stats = tweet.find_elements(By.XPATH, ".//div[@data-testid='like']//span")
                likes = int(stats[0].text.replace(",", "")) if stats else 0

                scraped_data.append({
                    "username": username,
                    "content": content,
                    "timestamp": timestamp,
                    "likes": likes,
                    "permalink": permalink,
                })

            except Exception as e:
                print(f"Failed to parse tweet: {e}")
                continue

        print(f"Scraping complete. Found {len(scraped_data)} tweets.")
        return pd.DataFrame(scraped_data)

    finally:
        if driver:
            print("Closing WebDriver.")
            driver.quit()
        print(f"Cleaning up temp dir: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    USERNAME = "seatedro"
    SCROLLS = 5
    PROXY = None
    tweet_df = scrape_x(USERNAME, SCROLLS, proxy=PROXY)

    if not tweet_df.empty:
        print("\n--- Scraped Data (First 5 Rows as JSON) ---")
        print(tweet_df.head().to_json(orient="records", indent=2))

        output_filename = f"x_scrape_{USERNAME}.json"
        tweet_df.to_json(output_filename, orient="records", indent=4)
        print(f"\nData saved to {output_filename}")
    else:
        print(f"\nNo tweets scraped for @{USERNAME}.")
