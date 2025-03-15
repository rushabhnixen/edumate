from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class UserActivity(models.Model):
    """
    Track user activities for analytics purposes.
    """
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('page_view', 'Page View'),
        ('course_view', 'Course View'),
        ('lesson_view', 'Lesson View'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('search', 'Search'),
        ('download', 'Download'),
        ('comment', 'Comment'),
        ('rating', 'Rating'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics_activities'
    )
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Generic foreign key to associate activity with any model
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='analytics_activities'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional data
    session_id = models.CharField(max_length=100, blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('User Activity')
        verbose_name_plural = _('User Activities')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class LearningInsight(models.Model):
    """
    AI-generated insights about user learning patterns.
    """
    INSIGHT_TYPES = (
        ('learning_pattern', 'Learning Pattern'),
        ('engagement', 'Engagement'),
        ('performance', 'Performance'),
        ('recommendation', 'Recommendation'),
        ('study_habit', 'Study Habit'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_insights')
    title = models.CharField(max_length=255, default="Learning Insight")
    description = models.TextField(blank=True, default="No description provided")
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Learning Insight')
        verbose_name_plural = _('Learning Insights')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class UserEngagement(models.Model):
    """
    Metrics for user engagement with the platform.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement_metrics'
    )
    date = models.DateField()
    time_spent = models.PositiveIntegerField(help_text=_("Time spent in seconds"))
    pages_visited = models.PositiveIntegerField(default=0)
    lessons_completed = models.PositiveIntegerField(default=0)
    quizzes_taken = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('User Engagement')
        verbose_name_plural = _('User Engagements')
        unique_together = ('user', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class UserPerformance(models.Model):
    """
    Track user performance metrics over time.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_metrics',
        verbose_name=_('User')
    )
    date = models.DateField(_('Date'))
    quiz_average_score = models.FloatField(_('Quiz Average Score'), null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(_('Time Spent (minutes)'), default=0)
    content_completed_count = models.PositiveIntegerField(_('Content Completed Count'), default=0)
    points_earned = models.PositiveIntegerField(_('Points Earned'), default=0)
    
    class Meta:
        verbose_name = _('User Performance')
        verbose_name_plural = _('User Performances')
        unique_together = [['user', 'date']]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - Performance on {self.date}"


class ContentDifficulty(models.Model):
    """
    Track difficulty ratings for content.
    """
    CONTENT_TYPES = (
        ('lesson', _('Lesson')),
        ('video', _('Video')),
        ('quiz', _('Quiz')),
        ('question', _('Question')),
    )
    
    content_type = models.CharField(
        _('Content Type'),
        max_length=10,
        choices=CONTENT_TYPES
    )
    content_id = models.PositiveIntegerField(_('Content ID'))
    difficulty_score = models.FloatField(_('Difficulty Score'), default=0.0)
    rating_count = models.PositiveIntegerField(_('Rating Count'), default=0)
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True)
    
    class Meta:
        verbose_name = _('Content Difficulty')
        verbose_name_plural = _('Content Difficulties')
        unique_together = [['content_type', 'content_id']]
    
    def __str__(self):
        return f"{self.get_content_type_display()} {self.content_id} - Difficulty: {self.difficulty_score}"


class UserContentDifficultyRating(models.Model):
    """
    Individual user ratings for content difficulty.
    """
    DIFFICULTY_CHOICES = (
        (1, _('Very Easy')),
        (2, _('Easy')),
        (3, _('Moderate')),
        (4, _('Difficult')),
        (5, _('Very Difficult')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='difficulty_ratings',
        verbose_name=_('User')
    )
    content_difficulty = models.ForeignKey(
        ContentDifficulty,
        on_delete=models.CASCADE,
        related_name='user_ratings',
        verbose_name=_('Content Difficulty')
    )
    rating = models.PositiveSmallIntegerField(
        _('Rating'),
        choices=DIFFICULTY_CHOICES
    )
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('User Content Difficulty Rating')
        verbose_name_plural = _('User Content Difficulty Ratings')
        unique_together = [['user', 'content_difficulty']]
    
    def __str__(self):
        return f"{self.user.username} - {self.content_difficulty} - Rating: {self.rating}" 