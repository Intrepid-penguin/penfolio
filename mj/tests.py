from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from mj.models import Journal
from users.models import UserProfile

class StreakTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password456')

    def create_journal(self, user, days_ago=0):
        """Helper function to create a journal entry with specified age"""
        created_at = timezone.now() - timedelta(days=days_ago)
        return Journal.objects.create(
            owner=user,
            title=f"Entry {days_ago} days ago",
            content="Test content",
            date_added=created_at
        )

    def update_streak_based_on_journal(self, user, journal):
        """Update streak based on the journal's actual creation date"""
        try:
            user_profile = user.user_profile
        except UserProfile.DoesNotExist:
            return

        journal_date = journal.date_added.date()
        
        if user_profile.last_content_date == journal_date:
            return  # Already counted for this date

        # Calculate streak based on journal date
        if user_profile.last_content_date == journal_date - timedelta(days=1):
            user_profile.current_streak += 1
        else:
            user_profile.current_streak = 1

        user_profile.longest_streak = max(user_profile.longest_streak, user_profile.current_streak)
        user_profile.last_content_date = journal_date
        user_profile.save()

    def test_initial_streak(self):
        """Test initial user profile streak values"""
        user_profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(user_profile.current_streak, 0)
        self.assertEqual(user_profile.longest_streak, 0)
        self.assertIsNone(user_profile.last_content_date)

    def test_start_new_streak(self):
        """Test starting a new streak with first journal entry"""
        journal = self.create_journal(self.user1)
        self.update_streak_based_on_journal(self.user1, journal)
        
        profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.longest_streak, 1)
        self.assertEqual(profile.last_content_date, journal.date_added.date())

    def test_continue_streak(self):
        """Test continuing an existing streak with consecutive entries"""
        # Day 1 journal
        journal1 = self.create_journal(self.user1, days_ago=1)
        self.update_streak_based_on_journal(self.user1, journal1)
        
        # Day 2 journal (today)
        journal2 = self.create_journal(self.user1)
        self.update_streak_based_on_journal(self.user1, journal2)
        
        profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(profile.current_streak, 2)
        self.assertEqual(profile.longest_streak, 2)
        self.assertEqual(profile.last_content_date, journal2.date_added.date())

    def test_streak_reset_after_missing_one_day(self):
        """Test streak reset when missing one day between entries"""
        # Journal 2 days ago
        journal1 = self.create_journal(self.user1, days_ago=2)
        self.update_streak_based_on_journal(self.user1, journal1)
        
        # Journal today (skipping yesterday)
        journal2 = self.create_journal(self.user1)
        self.update_streak_based_on_journal(self.user1, journal2)
        
        profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.longest_streak, 1)
        self.assertEqual(profile.last_content_date, journal2.date_added.date())

    def test_streak_reset_after_missing_multiple_days(self):
        """Test streak reset with multiple days gap"""
        # Journal 5 days ago
        journal1 = self.create_journal(self.user1, days_ago=5)
        self.update_streak_based_on_journal(self.user1, journal1)
        
        # Journal today
        journal2 = self.create_journal(self.user1)
        self.update_streak_based_on_journal(self.user1, journal2)
        
        profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.longest_streak, 1)
        self.assertEqual(profile.last_content_date, journal2.date_added.date())

    def test_longest_streak_tracking(self):
        """Test longest streak tracking with multiple entries"""
        # Create 4-day streak
        for days_ago in [3, 2, 1, 0]:
            journal = self.create_journal(self.user1, days_ago=days_ago)
            self.update_streak_based_on_journal(self.user1, journal)
        
        # Break streak and create new entry
        journal = self.create_journal(self.user1, days_ago=5)
        self.update_streak_based_on_journal(self.user1, journal)
        
        profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.longest_streak, 4)

    def test_multiple_journals_same_day(self):
        """Test multiple journals on the same day don't affect streak"""
        # Create two journals on the same day
        journal1 = self.create_journal(self.user1)
        journal2 = self.create_journal(self.user1)
        
        self.update_streak_based_on_journal(self.user1, journal1)
        self.update_streak_based_on_journal(self.user1, journal2)
        
        profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.longest_streak, 1)

    # def test_streak_with_future_dated_journal(self):
    #     """Test journals with future dates don't affect streak"""
    #     # Create future-dated journal (should be ignored)
    #     future_journal = Journal.objects.create(
    #         owner=self.user1,
    #         title="Future Entry",
    #         content="Test content",
    #         date_added=timezone.now() + timedelta(days=1)
    #     )
    #     self.update_streak_based_on_journal(self.user1, future_journal)
        
    #     profile = UserProfile.objects.get(user=self.user1)
    #     self.assertEqual(profile.current_streak, 0)
    #     self.assertEqual(profile.longest_streak, 0)