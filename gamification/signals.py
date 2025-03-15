from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count

from courses.models import Enrollment, Progress, QuizAttempt
from .models import (
    Badge, UserBadge, Achievement, UserAchievement,
    PointsTransaction, Streak, Leaderboard, UserChallenge
)

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_streak(sender, instance, created, **kwargs):
    """
    Create a streak record for new users.
    """
    if created:
        Streak.objects.create(user=instance)
        
        # Create initial leaderboard entry
        Leaderboard.objects.create(user=instance, points=0, rank=0)


@receiver(post_save, sender=PointsTransaction)
def update_user_points(sender, instance, created, **kwargs):
    """
    Update user points when a new transaction is created.
    """
    if created:
        user = instance.user
        # Calculate total points
        total_points = PointsTransaction.objects.filter(user=user).aggregate(Sum('points'))['points__sum'] or 0
        
        # Update user points
        user.points = total_points
        
        # Update user level based on points
        if total_points >= 1000:
            user.level = 5
        elif total_points >= 500:
            user.level = 4
        elif total_points >= 250:
            user.level = 3
        elif total_points >= 100:
            user.level = 2
        else:
            user.level = 1
            
        user.save(update_fields=['points', 'level'])
        
        # Update leaderboard
        leaderboard, created = Leaderboard.objects.get_or_create(user=user)
        leaderboard.points = total_points
        leaderboard.save()
        
        # Check for badge eligibility
        check_badge_eligibility(user)


def check_badge_eligibility(user):
    """Check if user is eligible for any badges based on points"""
    user_points = user.points
    user_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    
    # Get badges that user doesn't have and is eligible for
    eligible_badges = Badge.objects.filter(
        points_required__lte=user_points
    ).exclude(
        id__in=user_badges
    )
    
    # Award badges
    for badge in eligible_badges:
        UserBadge.objects.create(
            user=user,
            badge=badge
        )
        
        # Create notification or message
        # This could be implemented with a notification system


@receiver(post_save, sender=QuizAttempt)
def check_quiz_achievements(sender, instance, created, **kwargs):
    """
    Check for quiz-related achievements when a quiz is completed.
    """
    if created and instance.passed:
        user = instance.student
        
        # Update streak
        streak, created = Streak.objects.get_or_create(user=user)
        streak.update_streak()
        
        # Check for quiz score achievements
        quiz_achievements = Achievement.objects.filter(
            achievement_type='quiz_score'
        )
        
        for achievement in quiz_achievements:
            # Check if the score meets the threshold
            if instance.score_percentage >= achievement.threshold:
                # Check if already unlocked
                if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                    # Unlock achievement
                    UserAchievement.objects.create(
                        user=user,
                        achievement=achievement
                    )
                    
                    # Award badge if applicable
                    if achievement.badge:
                        UserBadge.objects.get_or_create(
                            user=user,
                            badge=achievement.badge
                        )
                    
                    # Award points
                    if achievement.points > 0:
                        PointsTransaction.objects.create(
                            user=user,
                            points=achievement.points,
                            transaction_type='bonus',
                            description=f"Achievement unlocked: {achievement.name}"
                        )


@receiver(post_save, sender=Enrollment)
def check_course_enrollment_achievements(sender, instance, created, **kwargs):
    """
    Check for course enrollment achievements.
    """
    if created:
        user = instance.student
        
        # Count total enrollments
        enrollment_count = Enrollment.objects.filter(student=user).count()
        
        # Check for enrollment achievements
        enrollment_achievements = Achievement.objects.filter(
            achievement_type='activity',
            description__icontains='enroll'
        )
        
        for achievement in enrollment_achievements:
            if enrollment_count >= achievement.threshold:
                # Check if already unlocked
                if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                    # Unlock achievement
                    UserAchievement.objects.create(
                        user=user,
                        achievement=achievement
                    )
                    
                    # Award badge if applicable
                    if achievement.badge:
                        UserBadge.objects.get_or_create(
                            user=user,
                            badge=achievement.badge
                        )
                    
                    # Award points
                    if achievement.points > 0:
                        PointsTransaction.objects.create(
                            user=user,
                            points=achievement.points,
                            transaction_type='bonus',
                            description=f"Achievement unlocked: {achievement.name}"
                        )


@receiver(post_save, sender=Progress)
def check_course_completion_achievements(sender, instance, **kwargs):
    """
    Check for course completion achievements.
    """
    # Calculate course completion percentage
    course_modules = instance.course.modules.count()
    if course_modules == 0:
        return
    
    user_progress = Progress.objects.filter(
        student=instance.student,
        course=instance.course
    )
    
    total_percentage = sum(p.completion_percentage for p in user_progress)
    overall_percentage = total_percentage / course_modules
    
    # If course is completed (100%)
    if overall_percentage >= 100:
        user = instance.student
        
        # Record course completion
        enrollment = Enrollment.objects.get(student=user, course=instance.course)
        enrollment.status = 'completed'
        enrollment.completion_date = timezone.now()
        enrollment.save()
        
        # Count completed courses
        completed_courses = Enrollment.objects.filter(
            student=user,
            status='completed'
        ).count()
        
        # Check for course completion achievements
        completion_achievements = Achievement.objects.filter(
            achievement_type='course_completion'
        )
        
        for achievement in completion_achievements:
            if completed_courses >= achievement.threshold:
                # Check if already unlocked
                if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                    # Unlock achievement
                    UserAchievement.objects.create(
                        user=user,
                        achievement=achievement
                    )
                    
                    # Award badge if applicable
                    if achievement.badge:
                        UserBadge.objects.get_or_create(
                            user=user,
                            badge=achievement.badge
                        )
                    
                    # Award points
                    if achievement.points > 0:
                        PointsTransaction.objects.create(
                            user=user,
                            points=achievement.points,
                            transaction_type='bonus',
                            description=f"Achievement unlocked: {achievement.name}"
                        )


@receiver(post_save, sender=Streak)
def check_streak_achievements(sender, instance, **kwargs):
    """
    Check for streak-related achievements.
    """
    user = instance.user
    
    # Check for streak achievements
    streak_achievements = Achievement.objects.filter(
        achievement_type='streak'
    )
    
    for achievement in streak_achievements:
        if instance.current_streak >= achievement.threshold:
            # Check if already unlocked
            if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                # Unlock achievement
                UserAchievement.objects.create(
                    user=user,
                    achievement=achievement
                )
                
                # Award badge if applicable
                if achievement.badge:
                    UserBadge.objects.get_or_create(
                        user=user,
                        badge=achievement.badge
                    )
                
                # Award points
                if achievement.points > 0:
                    PointsTransaction.objects.create(
                        user=user,
                        points=achievement.points,
                        transaction_type='bonus',
                        description=f"Achievement unlocked: {achievement.name}"
                    )


@receiver(post_save, sender=UserChallenge)
def check_challenge_completion(sender, instance, **kwargs):
    """Check if a challenge is completed and award points"""
    if instance.status == 'completed' and instance.completed_at is None:
        # Mark as completed
        instance.completed_at = timezone.now()
        instance.save(update_fields=['completed_at'])
        
        # Award points
        PointsTransaction.objects.create(
            user=instance.user,
            points=instance.challenge.points_reward,
            transaction_type='earned',
            description=f"Completed challenge: {instance.challenge.name}"
        )
        
        # Award badge if associated with challenge
        if instance.challenge.badge:
            UserBadge.objects.get_or_create(
                user=instance.user,
                badge=instance.challenge.badge
            )


@receiver(post_save, sender=Leaderboard)
def update_leaderboard_ranks(sender, instance, **kwargs):
    """Update ranks for all users in the leaderboard"""
    # This is a simple implementation that might not be efficient for large user bases
    # For production, consider using a scheduled task or more efficient approach
    leaderboards = Leaderboard.objects.all().order_by('-points')
    
    for i, leaderboard in enumerate(leaderboards, 1):
        if leaderboard.rank != i:
            leaderboard.rank = i
            leaderboard.save(update_fields=['rank']) 