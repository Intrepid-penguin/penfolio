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

from x import scrape_x

client = genai.Client(api_key=settings.GEMINI_API_KEY)

USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
]

def get_twitter_inspo(username: str, scrolls: int = 10, proxy: str = None):
  
  existing_cache = user_exists_in_cache(username)
  cache_dir = ".cache"
  
  if existing_cache:
    print(f"User '{username}' data already exists in cache. Loading from cache...")
    
    cache_file = os.path.join(cache_dir, f"{username}.json")
    return pd.read_json(cache_file, orient="records").to_json()
  
  tweet_df = scrape_x(username, scrolls, proxy)
  
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
Your response should be a single tweet text that reflects the user's unique style while conveying the essence of the journal entry. Do not include any explanations, justifications, or additional commentary—only the tweet text itself.

Your response must short and contain **ONLY** the generated tweet text. Do not include any introductory remarks, style analysis, or additional commentary.
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
