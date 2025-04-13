import os
import django
import random
from mj.models import Journal
# from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'm_journal.settings')
django.setup()


mood = [
    ('ME', 'Merry'),
    ('GL', 'Gloomy'),
    ('CO', 'Covert')
]

# create_sample_journals.py


# Sample data
titles = [
    "Morning Reflections", "Evening Thoughts", "A Day at Work", "Weekend Adventures",
    "Family Time", "Personal Growth", "Learning Journey", "Creative Moments",
    "Challenges Faced", "Grateful Hearts", "Dreams and Goals", "Quiet Moments",
    "Friendship Stories", "Travel Memories", "Simple Pleasures", "Life Lessons",
    "Seasonal Changes", "Inner Peace", "Daily Struggles", "Hopeful Tomorrow"
]

content_samples = [
    "Today was filled with unexpected moments that made me reflect on life's beautiful unpredictability.",
    "The morning sun reminded me of new beginnings and fresh opportunities ahead.",
    "Work brought its usual challenges, but I'm learning to navigate them with greater wisdom.",
    "Spent quality time with loved ones, creating memories that will last forever.",
    "Taking small steps towards my goals, one day at a time.",
    "Found joy in the simplest things today - a warm cup of coffee and good conversation.",
    "Reflecting on personal growth and the journey that brought me to this moment.",
    "Creative energy was flowing today, inspiring new ideas and perspectives.",
    "Faced some difficulties but emerged stronger and more resilient.",
    "Counting my blessings and appreciating the good things in my life."
]

moods = ['ME', 'GL', 'CO']

def create_sample_journals():
    """Create 20 sample journal entries."""
    for i in range(20):
        # Create random date within last 30 days
        # days_ago = random.randint(0, 30)
        # created_date = datetime.now() - timedelta(days=days_ago)
        
        journal = Journal.objects.create(
            title=titles[i],
            content=random.choice(content_samples),
            mood_tag=random.choice(moods),
            owner_id= 1
        )
        print(f"Created journal {i+1}: {journal.title}")

if __name__ == "__main__":
    create_sample_journals()
    print("Successfully created 20 sample journals!")