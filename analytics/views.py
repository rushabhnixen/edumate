from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, F, Q
from django.utils import timezone
from datetime import timedelta
import json
import openai
import numpy as np
from collections import Counter
from django.contrib.contenttypes.models import ContentType

from .models import (
    UserActivity, LearningInsight, UserPerformance,
    ContentDifficulty, UserContentDifficultyRating,
    LearningStyle, AILearningRecommendation
)
from courses.models import Enrollment, Progress, QuizAttempt, Course, Lesson, Quiz
from gamification.models import UserAchievement, UserBadge, PointsTransaction
from .utils import (
    generate_learning_insights, generate_learning_recommendations,
    detect_learning_style, get_user_learning_data
)


@login_required
def dashboard(request):
    """
    User analytics dashboard showing learning progress and insights.
    """
    user = request.user
    
    # Detect learning style if not already set
    learning_style = LearningStyle.objects.filter(user=user).first()
    if not learning_style:
        learning_style = detect_learning_style(user)
    
    # Get recent activities
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
    
    # Get learning insights
    insights = LearningInsight.objects.filter(user=user).order_by('-generated_at')[:5]
    if not insights.exists():
        # Generate initial insights if none exist
        insights = generate_learning_insights(user, insight_count=3)
    
    # Get recommendations
    recommendations = AILearningRecommendation.objects.filter(
        user=user,
        is_dismissed=False,
        is_completed=False
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).order_by('-created_at')[:3]
    
    if not recommendations.exists():
        # Generate initial recommendations if none exist
        recommendations = generate_learning_recommendations(user, count=3)
    
    # Get performance metrics for the last 30 days
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    performance = UserPerformance.objects.filter(
        user=user,
        date__gte=thirty_days_ago
    ).order_by('date')
    
    # Get course progress
    enrollments = Enrollment.objects.filter(student=user).select_related('course')
    
    # Calculate progress for each course
    for enrollment in enrollments:
        course = enrollment.course
        progress_records = Progress.objects.filter(
            student=user,
            course=course
        )
        
        if progress_records.exists():
            total_percentage = sum(p.completion_percentage for p in progress_records)
            enrollment.overall_progress = total_percentage / progress_records.count()
        else:
            enrollment.overall_progress = 0
    
    # Get quiz performance
    quiz_attempts = QuizAttempt.objects.filter(user=user).order_by('-completed_at')[:10]
    avg_quiz_score = QuizAttempt.objects.filter(user=user).aggregate(avg=Avg('score'))['avg'] or 0
    
    # Get points history
    points_history = PointsTransaction.objects.filter(user=user).order_by('-timestamp')[:10]
    
    # Get achievements and badges
    achievements = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-date_earned')[:5]
    badges = UserBadge.objects.filter(user=user).select_related('badge').order_by('-earned_at')[:5]
    
    context = {
        'recent_activities': recent_activities,
        'insights': insights,
        'recommendations': recommendations,
        'learning_style': learning_style,
        'performance': performance,
        'enrollments': enrollments,
        'quiz_attempts': quiz_attempts,
        'avg_quiz_score': avg_quiz_score,
        'points_history': points_history,
        'achievements': achievements,
        'badges': badges,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def learning_insights(request):
    """
    Display AI-generated learning insights for the user.
    """
    user = request.user
    
    # Get all insights
    insights = LearningInsight.objects.filter(user=user).order_by('-generated_at')
    
    # Mark insights as read
    unread_insights = insights.filter(is_read=False)
    unread_insights.update(is_read=True)
    
    # Group insights by type
    learning_pattern_insights = insights.filter(insight_type='learning_pattern')
    engagement_insights = insights.filter(insight_type='engagement')
    performance_insights = insights.filter(insight_type='performance')
    recommendation_insights = insights.filter(insight_type='recommendation')
    study_habit_insights = insights.filter(insight_type='study_habit')
    strength_insights = insights.filter(insight_type='strength')
    weakness_insights = insights.filter(insight_type='weakness')
    learning_style_insights = insights.filter(insight_type='learning_style')
    improvement_insights = insights.filter(insight_type='improvement')
    
    context = {
        'insights': insights,
        'learning_pattern_insights': learning_pattern_insights,
        'engagement_insights': engagement_insights,
        'performance_insights': performance_insights,
        'recommendation_insights': recommendation_insights,
        'study_habit_insights': study_habit_insights,
        'strength_insights': strength_insights,
        'weakness_insights': weakness_insights,
        'learning_style_insights': learning_style_insights,
        'improvement_insights': improvement_insights,
    }
    
    return render(request, 'analytics/learning_insights.html', context)


@login_required
def generate_insight(request):
    """
    Generate a new AI insight for the user.
    """
    if request.method != 'POST':
        return redirect('analytics:learning_insights')
    
    user = request.user
    
    # Generate new insights using AI
    try:
        insights = generate_learning_insights(user, insight_count=1)
        if insights:
            return redirect('analytics:learning_insights')
        
    except Exception as e:
        # Fallback if AI generation fails
        LearningInsight.objects.create(
            user=user,
            title="Learning Recommendation",
            description=f"Based on your recent activity, we recommend continuing to engage with your courses regularly to maintain your learning momentum.",
            insight_type='recommendation',
            relevance_score=0.7
        )
    
    return redirect('analytics:learning_insights')


@login_required
def generate_recommendation(request):
    """
    Generate a new AI recommendation for the user.
    """
    if request.method != 'POST':
        return redirect('analytics:dashboard')
    
    user = request.user
    
    # Generate new recommendations using AI
    try:
        recommendations = generate_learning_recommendations(user, count=1)
        if recommendations:
            return redirect('analytics:dashboard')
        
    except Exception as e:
        # Fallback if AI generation fails
        AILearningRecommendation.objects.create(
            user=user,
            title="Continue Your Learning Journey",
            description="We recommend continuing with your current courses and focusing on completing one module at a time for better retention.",
            recommendation_type='study_technique',
            urgency='medium',
            confidence_score=0.6,
            expires_at=timezone.now() + timedelta(days=30)
        )
    
    return redirect('analytics:dashboard')


@login_required
def learning_style_view(request):
    """
    Display and update a user's learning style information.
    """
    user = request.user
    
    # Get or detect learning style
    learning_style = LearningStyle.objects.filter(user=user).first()
    if not learning_style:
        learning_style = detect_learning_style(user)
        
        # If still no data, create default
        if not learning_style:
            learning_style = LearningStyle.objects.create(user=user)
    
    if request.method == 'POST':
        # Update learning style based on form submission
        primary_style = request.POST.get('primary_style')
        secondary_style = request.POST.get('secondary_style')
        pace_preference = request.POST.get('pace_preference')
        prefers_group = request.POST.get('prefers_group_learning') == 'true'
        prefers_examples = request.POST.get('prefers_practical_examples') == 'true'
        prefers_theory = request.POST.get('prefers_theory_first') == 'true'
        attention_span = int(request.POST.get('attention_span_minutes', 30))
        
        # Update learning style
        learning_style.primary_style = primary_style
        learning_style.secondary_style = secondary_style
        learning_style.pace_preference = pace_preference
        learning_style.prefers_group_learning = prefers_group
        learning_style.prefers_practical_examples = prefers_examples
        learning_style.prefers_theory_first = prefers_theory
        learning_style.attention_span_minutes = attention_span
        learning_style.save()
        
        # Generate a learning style insight
        LearningInsight.objects.create(
            user=user,
            title="Updated Learning Style",
            description=f"Your learning style has been updated. You prefer a {learning_style.get_primary_style_display()} learning style with a {learning_style.get_pace_preference_display()} pace.",
            insight_type='learning_style',
            relevance_score=0.9
        )
        
        return redirect('analytics:learning_style')
    
    # Get activities data for visualization
    visual_count = UserActivity.objects.filter(
        user=user,
        activity_type__in=['video_view', 'image_view']
    ).count()
    
    auditory_count = UserActivity.objects.filter(
        user=user,
        activity_type__in=['audio_view', 'video_view']
    ).count()
    
    reading_count = UserActivity.objects.filter(
        user=user,
        activity_type__in=['lesson_view', 'document_view', 'article_view']
    ).count()
    
    kinesthetic_count = UserActivity.objects.filter(
        user=user,
        activity_type__in=['quiz_attempt', 'interactive_activity']
    ).count()
    
    activity_counts = {
        'Visual': visual_count,
        'Auditory': auditory_count,
        'Reading/Writing': reading_count,
        'Kinesthetic': kinesthetic_count
    }
    
    context = {
        'learning_style': learning_style,
        'activity_counts': activity_counts,
    }
    
    return render(request, 'analytics/learning_style.html', context)


@login_required
def dismiss_recommendation(request, recommendation_id):
    """
    Mark a recommendation as dismissed.
    """
    if request.method != 'POST':
        return redirect('analytics:dashboard')
        
    recommendation = get_object_or_404(
        AILearningRecommendation, 
        id=recommendation_id,
        user=request.user
    )
    
    recommendation.is_dismissed = True
    recommendation.save()
    
    return redirect('analytics:dashboard')


@login_required
def complete_recommendation(request, recommendation_id):
    """
    Mark a recommendation as completed.
    """
    if request.method != 'POST':
        return redirect('analytics:dashboard')
        
    recommendation = get_object_or_404(
        AILearningRecommendation, 
        id=recommendation_id,
        user=request.user
    )
    
    recommendation.is_completed = True
    recommendation.save()
    
    # Award points for completing a recommendation
    PointsTransaction.objects.create(
        user=request.user,
        points=10,
        transaction_type='earned',
        description=f"Completed recommendation: {recommendation.title}"
    )
    
    return redirect('analytics:dashboard')


@login_required
def rate_content_difficulty(request):
    """
    AJAX endpoint for users to rate content difficulty.
    """
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        content_id = request.POST.get('content_id')
        rating = int(request.POST.get('rating'))
        
        if content_type and content_id and 1 <= rating <= 5:
            # Get or create content difficulty record
            content_difficulty, created = ContentDifficulty.objects.get_or_create(
                content_type=content_type,
                content_id=content_id,
                defaults={'difficulty_score': rating, 'rating_count': 1}
            )
            
            if not created:
                # Check if user has already rated this content
                existing_rating = UserContentDifficultyRating.objects.filter(
                    user=request.user,
                    content_difficulty=content_difficulty
                ).first()
                
                if existing_rating:
                    # Update existing rating
                    old_rating = existing_rating.rating
                    existing_rating.rating = rating
                    existing_rating.save()
                    
                    # Update content difficulty score
                    total_score = (content_difficulty.difficulty_score * content_difficulty.rating_count) - old_rating + rating
                    content_difficulty.difficulty_score = total_score / content_difficulty.rating_count
                    content_difficulty.save()
                else:
                    # Add new rating
                    UserContentDifficultyRating.objects.create(
                        user=request.user,
                        content_difficulty=content_difficulty,
                        rating=rating
                    )
                    
                    # Update content difficulty score
                    total_score = (content_difficulty.difficulty_score * content_difficulty.rating_count) + rating
                    content_difficulty.rating_count += 1
                    content_difficulty.difficulty_score = total_score / content_difficulty.rating_count
                    content_difficulty.save()
            
            return JsonResponse({'success': True, 'new_score': content_difficulty.difficulty_score})
        
        return JsonResponse({'success': False, 'error': 'Invalid rating parameters'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


class InstructorDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Dashboard for instructors to view analytics about their courses.
    """
    template_name = 'analytics/instructor_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_instructor() or self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get courses taught by this instructor
        courses = Course.objects.filter(instructor=user)
        
        # Get enrollment stats
        enrollment_stats = []
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course)
            total_enrollments = enrollments.count()
            completed = enrollments.filter(status='completed').count()
            dropped = enrollments.filter(status='dropped').count()
            
            # Calculate average progress
            progress_records = Progress.objects.filter(course=course)
            if progress_records.exists():
                avg_progress = progress_records.aggregate(avg=Avg('completion_percentage'))['avg'] or 0
            else:
                avg_progress = 0
            
            # Calculate quiz performance
            course_quizzes = QuizAttempt.objects.filter(quiz__module__course=course)
            avg_quiz_score = course_quizzes.aggregate(avg=Avg('score'))['avg'] or 0
            pass_rate = course_quizzes.filter(passed=True).count() / course_quizzes.count() if course_quizzes.count() > 0 else 0
            
            enrollment_stats.append({
                'course': course,
                'total_enrollments': total_enrollments,
                'completed': completed,
                'dropped': dropped,
                'avg_progress': avg_progress,
                'avg_quiz_score': avg_quiz_score,
                'pass_rate': pass_rate,
            })
        
        context['enrollment_stats'] = enrollment_stats
        context['courses'] = courses
        
        return context


class CourseAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Detailed analytics for a specific course.
    """
    template_name = 'analytics/course_analytics.html'
    context_object_name = 'course'
    
    def test_func(self):
        return self.request.user.is_instructor() or self.request.user.is_staff
    
    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Get enrollment data
        enrollments = Enrollment.objects.filter(course=course)
        enrollment_count = enrollments.count()
        completion_count = enrollments.filter(status='completed').count()
        
        # Get progress data
        progress_records = Progress.objects.filter(course=course)
        
        # Get module completion data
        module_data = []
        for module in course.modules.all():
            module_progress = progress_records.filter(module=module)
            completion_percentage = module_progress.aggregate(avg=Avg('completion_percentage'))['avg'] or 0
            
            module_data.append({
                'module': module,
                'completion_percentage': completion_percentage,
            })
        
        # Get quiz performance data
        quiz_data = []
        for module in course.modules.all():
            for quiz in module.contents.filter(quiz__isnull=False):
                quiz_attempts = QuizAttempt.objects.filter(quiz=quiz.quiz)
                avg_score = quiz_attempts.aggregate(avg=Avg('score'))['avg'] or 0
                pass_rate = quiz_attempts.filter(passed=True).count() / quiz_attempts.count() if quiz_attempts.count() > 0 else 0
                
                quiz_data.append({
                    'quiz': quiz.quiz,
                    'attempts': quiz_attempts.count(),
                    'avg_score': avg_score,
                    'pass_rate': pass_rate,
                })
        
        # Get content difficulty ratings
        difficulty_data = []
        for module in course.modules.all():
            for content in module.contents.all():
                if hasattr(content, 'lesson'):
                    content_type = 'lesson'
                    content_id = content.lesson.id
                elif hasattr(content, 'video'):
                    content_type = 'video'
                    content_id = content.video.id
                elif hasattr(content, 'quiz'):
                    content_type = 'quiz'
                    content_id = content.quiz.id
                else:
                    continue
                
                difficulty = ContentDifficulty.objects.filter(
                    content_type=content_type,
                    content_id=content_id
                ).first()
                
                if difficulty:
                    difficulty_data.append({
                        'content': content,
                        'difficulty_score': difficulty.difficulty_score,
                        'rating_count': difficulty.rating_count,
                    })
        
        context.update({
            'enrollment_count': enrollment_count,
            'completion_count': completion_count,
            'completion_rate': (completion_count / enrollment_count * 100) if enrollment_count > 0 else 0,
            'module_data': module_data,
            'quiz_data': quiz_data,
            'difficulty_data': difficulty_data,
        })
        
        return context


@login_required
def log_activity(request):
    """
    AJAX endpoint to log user activity.
    """
    if request.method == 'POST':
        activity_type = request.POST.get('activity_type')
        details = request.POST.get('details', '{}')
        
        if activity_type:
            try:
                details_dict = json.loads(details)
                
                # Create activity record
                UserActivity.objects.create(
                    user=request.user,
                    activity_type=activity_type,
                    content_type=ContentType.objects.get_for_model(course),
                    object_id=course.id
                )
                
                # Update user's last activity date for streak tracking
                request.user.last_activity_date = timezone.now().date()
                request.user.save(update_fields=['last_activity_date'])
                
                # Update streak if applicable
                from gamification.models import Streak
                streak, created = Streak.objects.get_or_create(user=request.user)
                streak.update_streak()
                
                return JsonResponse({'success': True})
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON in details'})
        
        return JsonResponse({'success': False, 'error': 'Activity type is required'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def student_analytics_dashboard(request):
    """
    Display analytics dashboard for students.
    """
    user = request.user
    
    # Get recent activities
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
    
    # Get learning progress
    enrollments = Enrollment.objects.filter(student=user).select_related('course')
    
    # Get quiz performance
    quiz_attempts = QuizAttempt.objects.filter(user=user)
    avg_score = quiz_attempts.aggregate(avg=Avg('score'))['avg'] or 0
    recent_quizzes = quiz_attempts.order_by('-completed_at')[:5]
    
    # Get user performance metrics
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    performance = UserPerformance.objects.filter(
        user=user,
        date__gte=thirty_days_ago
    ).order_by('date')
    
    # Get user badges and achievements
    badges = UserBadge.objects.filter(user=user).select_related('badge')
    achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    
    # Get personalized recommendations
    recommendations = get_personalized_course_recommendations(user)
    
    # Get learning insights
    insights = LearningInsight.objects.filter(user=user, is_read=False).order_by('-generated_at')[:3]
    
    context = {
        'recent_activities': recent_activities,
        'enrollments': enrollments,
        'avg_score': avg_score,
        'recent_quizzes': recent_quizzes,
        'performance': performance,
        'badges': badges,
        'achievements': achievements,
        'recommendations': recommendations,
        'insights': insights,
    }
    
    return render(request, 'analytics/student_dashboard.html', context)


@login_required
def instructor_analytics_dashboard(request):
    """
    Display analytics dashboard for instructors with course and student insights.
    """
    user = request.user
    
    if not user.is_instructor:
        return redirect('accounts:dashboard')
    
    # Get instructor's courses
    instructor_courses = Course.objects.filter(instructor=user)
    
    # Get enrollment data
    course_enrollments = []
    for course in instructor_courses:
        enrollments = course.enrollments.count()
        course_enrollments.append({
            'course': course,
            'enrollments': enrollments,
            'completion_rate': calculate_completion_rate(course),
            'avg_rating': course.rating_set.aggregate(Avg('rating'))['rating__avg'] or 0,
        })
    
    # Get quiz performance data across all courses
    quiz_performance = []
    for course in instructor_courses:
        quizzes = Quiz.objects.filter(lesson__module__course=course)
        for quiz in quizzes:
            attempts = QuizAttempt.objects.filter(quiz=quiz)
            if attempts.exists():
                avg_score = attempts.aggregate(Avg('score'))['score__avg'] or 0
                quiz_performance.append({
                    'quiz': quiz,
                    'course': course,
                    'avg_score': avg_score,
                    'attempts': attempts.count(),
                })
    
    # Get student engagement data
    student_engagement = analyze_student_engagement(instructor_courses)
    
    context = {
        'course_enrollments': course_enrollments,
        'quiz_performance': quiz_performance,
        'student_engagement': student_engagement,
    }
    
    return render(request, 'analytics/instructor_dashboard.html', context)


def get_personalized_course_recommendations(user, limit=5):
    """
    Generate personalized course recommendations based on user's performance and interests.
    """
    # Get courses the user is already enrolled in - changed from enrollment__student to enrollments__student
    enrolled_courses = Course.objects.filter(enrollments__student=user)
    
    # Get user's quiz performance to identify strengths and weaknesses
    quiz_attempts = QuizAttempt.objects.filter(user=user)
    
    # If user has no quiz attempts, recommend popular courses
    if not quiz_attempts.exists():
        return Course.objects.exclude(id__in=enrolled_courses).annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:limit]
    
    # Identify topics the user performs well in
    strong_topics = []
    weak_topics = []
    
    for attempt in quiz_attempts:
        quiz = attempt.quiz
        if attempt.score >= 80:  # User is strong in this topic
            strong_topics.append(quiz.lesson.title)
        elif attempt.score <= 50:  # User is weak in this topic
            weak_topics.append(quiz.lesson.title)
    
    # Count occurrences of each topic
    strong_topic_counts = Counter(strong_topics)
    weak_topic_counts = Counter(weak_topics)
    
    # Get most common strong and weak topics
    most_common_strong = [topic for topic, _ in strong_topic_counts.most_common(3)]
    most_common_weak = [topic for topic, _ in weak_topic_counts.most_common(3)]
    
    # Recommend courses that cover user's weak topics (for improvement)
    # and are related to user's strong topics (for interest)
    recommended_courses = Course.objects.exclude(id__in=enrolled_courses).filter(
        Q(module__lesson__title__in=most_common_weak) | 
        Q(module__lesson__title__in=most_common_strong)
    ).distinct()
    
    # If not enough recommendations, add popular courses
    if recommended_courses.count() < limit:
        popular_courses = Course.objects.exclude(
            id__in=enrolled_courses
        ).exclude(
            id__in=recommended_courses
        ).annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')
        
        # Combine the recommendations
        recommended_courses = list(recommended_courses) + list(popular_courses)
        
    return recommended_courses[:limit]


def identify_weak_areas(user):
    """
    Identify areas where the user needs improvement based on quiz performance.
    """
    # Get user's quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(user=user)
    
    if not quiz_attempts.exists():
        return []
    
    # Group attempts by lesson/topic and calculate average score
    topic_scores = {}
    for attempt in quiz_attempts:
        topic = attempt.quiz.lesson.title
        if topic not in topic_scores:
            topic_scores[topic] = {'total': 0, 'count': 0}
        
        topic_scores[topic]['total'] += attempt.score
        topic_scores[topic]['count'] += 1
    
    # Calculate average score for each topic
    for topic in topic_scores:
        topic_scores[topic]['avg'] = topic_scores[topic]['total'] / topic_scores[topic]['count']
    
    # Identify weak areas (topics with average score below 70%)
    weak_areas = [
        {'topic': topic, 'avg_score': data['avg']} 
        for topic, data in topic_scores.items() 
        if data['avg'] < 70
    ]
    
    # Sort by average score (ascending)
    weak_areas.sort(key=lambda x: x['avg_score'])
    
    return weak_areas


def calculate_completion_rate(course):
    """
    Calculate the completion rate for a course.
    """
    enrollments = course.enrollments.count()
    if enrollments == 0:
        return 0
    
    completed = course.enrollments.filter(completed=True).count()
    return (completed / enrollments) * 100


def analyze_student_engagement(courses):
    """
    Analyze student engagement across multiple courses.
    """
    engagement_data = []
    
    for course in courses:
        # Get all students enrolled in the course
        enrollments = course.enrollments.all()
        
        # Calculate engagement metrics
        total_students = enrollments.count()
        if total_students == 0:
            continue
            
        active_students = enrollments.filter(
            user__analytics_activities__timestamp__gte=timezone.now() - timezone.timedelta(days=7),
            user__analytics_activities__course=course
        ).distinct().count()
        
        completion_percentage = calculate_completion_rate(course)
        
        # Calculate average time spent
        activities = UserActivity.objects.filter(course=course)
        avg_time_spent = activities.aggregate(Avg('time_spent'))['time_spent__avg'] or 0
        
        engagement_data.append({
            'course': course,
            'total_students': total_students,
            'active_students': active_students,
            'active_percentage': (active_students / total_students) * 100 if total_students > 0 else 0,
            'completion_percentage': completion_percentage,
            'avg_time_spent': avg_time_spent,
        })
    
    return engagement_data 