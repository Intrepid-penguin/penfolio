# import logging
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.conf import settings
# from django.urls import reverse
# from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
# from requests_oauthlib import OAuth1Session

# # Configure logging (optional)
# logger = logging.getLogger(__name__)

# # X API OAuth 1.0a endpoints
# REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
# AUTHORIZE_URL = 'https://api.twitter.com/oauth/authorize'
# ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'


# def connect_page(request: HttpRequest) -> HttpResponse:
#     """Displays a simple page with a button/link to start the auth process."""
#     return render(request, 'users/connect.html') # Create this template


# def success_page(request: HttpRequest) -> HttpResponse:
#     """Displays a simple success page after authorization."""
#     # You might want to fetch user details here using the stored tokens
#     screen_name = request.session.get('twitter_screen_name', 'User')
#     return render(request, 'users/success.html', {'screen_name': screen_name}) # Create this template


# # === Step 1: Authorize ===
# def twitter_authorize(request: HttpRequest) -> HttpResponseRedirect:
#     """
#     Redirects the user to Twitter to grant permissions to your app.
#     """
#     try:
#         # --- 1. Get Request Token ---
#         # Build the callback URL dynamically (important!)
#         callback_uri = request.build_absolute_uri(reverse('twitter_callback'))
#         print(f"DEBUG: Callback URI: {callback_uri}") # Debug print

#         # Create an OAuth1Session instance (Consumer Key/Secret, Callback URI)
#         oauth = OAuth1Session(
#             client_key=settings.X_API_KEY,
#             client_secret=settings.X_API_SECRET,
#             callback_uri=callback_uri
#         )

#         # Fetch the Request Token from Twitter
#         fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
#         print(f"DEBUG: Fetch Response: {fetch_response}") # Debug print


#         # Extract the Request Token and Secret from the response
#         resource_owner_key = fetch_response.get('oauth_token')
#         resource_owner_secret = fetch_response.get('oauth_token_secret')
#         # Check if Twitter confirmed the callback (useful for debugging)
#         callback_confirmed = fetch_response.get('oauth_callback_confirmed') == 'true'

#         if not resource_owner_key or not resource_owner_secret or not callback_confirmed:
#             logger.error("OAuth callback not confirmed or tokens missing in response.")
#             # Redirect to an error page or show a message
#             return redirect('connect_page') # Or a dedicated error page

#         # --- 2. Store Request Token Secret in Session ---
#         # This secret is needed in the callback step to get the Access Token
#         request.session['oauth_token_secret'] = resource_owner_secret
#         request.session['oauth_token'] = resource_owner_key # Store token too if needed for verification
#         print(f"DEBUG: Stored oauth_token_secret in session: {resource_owner_secret[:5]}...") # Debug print

#         # --- 3. Redirect User to Twitter Authorization URL ---
#         authorization_url = oauth.authorization_url(AUTHORIZE_URL)
#         print(f"DEBUG: Redirecting user to: {authorization_url}") # Debug print

#         return HttpResponseRedirect(authorization_url)

#     except Exception as e:
#         logger.exception("Error during Twitter authorization initiation:")
#         # Handle error appropriately, maybe redirect to an error page
#         return HttpResponse(f"An error occurred: {e}", status=500)


# # === Step 2: Callback ===
# def twitter_callback(request: HttpRequest) -> HttpResponseRedirect:
#     """
#     Handles the callback from Twitter after the user authorizes the app.
#     Exchanges the Request Token and Verifier for an Access Token.
#     """
#     try:
#         oauth_token = request.GET.get('oauth_token')
#         oauth_verifier = request.GET.get('oauth_verifier')
#         denied = request.GET.get('denied')
#         if denied:
#             logger.warning(f"User denied access for request token: {denied}")
#             return redirect('login')
#         if not oauth_verifier or not oauth_token:
#             logger.error("OAuth verifier or token missing in callback request.")
#             return redirect('login')

#         resource_owner_secret = request.session.get('oauth_token_secret')

#         if not resource_owner_secret:
#             logger.error("OAuth token secret not found in session. Session might have expired.")
#             return redirect('twitter_authorize')

#         oauth = OAuth1Session(
#             client_key=settings.X_API_KEY,
#             client_secret=settings.X_API_SECRET,
#             resource_owner_key=oauth_token,        
#             resource_owner_secret=resource_owner_secret,
#             verifier=oauth_verifier
#         )

#         # Fetch the Access Token from Twitter
#         access_token_response = oauth.fetch_access_token(ACCESS_TOKEN_URL)
#         print(f"DEBUG: Access Token Response: {access_token_response}") # Debug print


#         # --- 4. Extract and Store Final User Tokens ---
#         final_oauth_token = access_token_response.get('oauth_token')
#         final_oauth_token_secret = access_token_response.get('oauth_token_secret')
#         user_id = access_token_response.get('user_id')
#         screen_name = access_token_response.get('screen_name')
        
#         print(f"DEBUG: Final OAuth Token: {access_token_response}") # Debug print

#         if not final_oauth_token or not final_oauth_token_secret:
#              logger.error("Access token or secret missing in response.")
#              return redirect('connect_page') # Or an error page

#         # **IMPORTANT: Store these securely!**
#         # Associate them with the logged-in Django user (request.user if using auth)
#         # Example: Storing in session (OK for demo, use DB for production)
#         request.session['twitter_access_token'] = final_oauth_token
#         request.session['twitter_access_token_secret'] = final_oauth_token_secret
#         request.session['twitter_user_id'] = user_id
#         request.session['twitter_screen_name'] = screen_name
#         print(f"DEBUG: Stored final access token for {screen_name} in session.")

#         # Clean up temporary session data
#         if 'oauth_token_secret' in request.session:
#             del request.session['oauth_token_secret']
#         if 'oauth_token' in request.session:
#             del request.session['oauth_token']

#         # --- 5. Redirect to Success Page ---
#         messages.success(request, f'Authorization successful for {screen_name}!')
#         return redirect('home')

#     except Exception as e:
#         logger.exception("Error during Twitter callback handling:")
#         # Handle error appropriately
#         return HttpResponse(f"An error occurred during callback: {e}", status=500)

import time
import pandas as pd
import random
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