from django.contrib import admin
from .models import (
    UserActivity, LearningInsight, UserPerformance,
    ContentDifficulty, UserContentDifficultyRating
)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['user__username', 'details']
    date_hierarchy = 'timestamp'


@admin.register(LearningInsight)
class LearningInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight_type', 'generated_at', 'is_read']
    list_filter = ['insight_type', 'is_read', 'generated_at']
    search_fields = ['user__username', 'description', 'title']
    date_hierarchy = 'generated_at'


@admin.register(UserPerformance)
class UserPerformanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'quiz_average_score', 'time_spent_minutes', 'content_completed_count', 'points_earned']
    list_filter = ['date']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(ContentDifficulty)
class ContentDifficultyAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'content_id', 'difficulty_score', 'rating_count', 'last_updated']
    list_filter = ['content_type', 'last_updated']
    search_fields = ['content_id']


@admin.register(UserContentDifficultyRating)
class UserContentDifficultyRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_difficulty', 'rating', 'timestamp']
    list_filter = ['rating', 'timestamp']
    search_fields = ['user__username']
    date_hierarchy = 'timestamp' 