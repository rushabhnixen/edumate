import json
import openai
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Count, Sum, F, Q
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType

from .models import (
    LearningInsight, UserActivity, UserPerformance,
    LearningStyle, AILearningRecommendation
)
from courses.models import (
    Enrollment, Progress, QuizAttempt, Course,
    Lesson, Quiz, Module
)
from gamification.models import UserAchievement, UserBadge, PointsTransaction


def get_user_learning_data(user):
    """
    Gather comprehensive learning data for a user to facilitate AI analysis.
    """
    # Time range for analysis
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    # Quiz performance
    quiz_attempts = QuizAttempt.objects.filter(user=user)
    recent_quiz_attempts = quiz_attempts.filter(completed_at__date__gte=thirty_days_ago)
    
    avg_score = quiz_attempts.aggregate(avg=Avg('score'))['avg'] or 0
    recent_avg_score = recent_quiz_attempts.aggregate(avg=Avg('score'))['avg'] or 0
    
    quiz_data = {
        'average_score': avg_score,
        'recent_average_score': recent_avg_score,
        'total_attempts': quiz_attempts.count(),
        'recent_attempts': recent_quiz_attempts.count(),
        'pass_rate': quiz_attempts.filter(passed=True).count() / max(1, quiz_attempts.count()) * 100,
        'recent_quiz_details': list(recent_quiz_attempts.values(
            'quiz__title', 'score', 'time_spent', 'passed'
        )[:10]),
    }
    
    # Course progress
    enrollments = Enrollment.objects.filter(student=user)
    courses_data = []
    
    for enrollment in enrollments:
        progress_records = Progress.objects.filter(
            student=user, 
            course=enrollment.course
        )
        
        if progress_records.exists():
            total_percentage = sum(p.completion_percentage for p in progress_records)
            overall_progress = total_percentage / progress_records.count()
            
            # Get recent progress (last 30 days)
            recent_activity = UserActivity.objects.filter(
                user=user,
                timestamp__date__gte=thirty_days_ago,
                content_type=ContentType.objects.get_for_model(enrollment.course),
                object_id=enrollment.course.id
            ).count()
            
            courses_data.append({
                'title': enrollment.course.title,
                'progress': overall_progress,
                'status': enrollment.status,
                'enrolled_date': enrollment.enrolled_at.strftime('%Y-%m-%d'),
                'recent_activity_count': recent_activity,
            })
    
    # User activity patterns
    activities = UserActivity.objects.filter(user=user)
    recent_activities = activities.filter(timestamp__date__gte=thirty_days_ago)
    
    activity_data = {
        'total_count': activities.count(),
        'recent_count': recent_activities.count(),
        'by_type': dict(recent_activities.values('activity_type').annotate(count=Count('id')).values_list('activity_type', 'count')),
        'by_hour': dict(recent_activities.extra({'hour': "EXTRACT(HOUR FROM timestamp)"}).values('hour').annotate(count=Count('id')).values_list('hour', 'count')),
        'by_day': dict(recent_activities.extra({'day': "EXTRACT(DOW FROM timestamp)"}).values('day').annotate(count=Count('id')).values_list('day', 'count')),
    }
    
    # Performance metrics
    performance_records = UserPerformance.objects.filter(
        user=user,
        date__gte=thirty_days_ago
    ).order_by('date')
    
    performance_data = {
        'daily_metrics': list(performance_records.values(
            'date', 'quiz_average_score', 'time_spent_minutes', 'content_completed_count', 'points_earned'
        )),
        'total_time_spent': performance_records.aggregate(total=Sum('time_spent_minutes'))['total'] or 0,
        'content_completed': performance_records.aggregate(total=Sum('content_completed_count'))['total'] or 0,
    }
    
    # Gamification data
    gamification_data = {
        'total_points': user.points if hasattr(user, 'points') else PointsTransaction.objects.filter(
            user=user, 
            transaction_type__in=['earned', 'bonus']
        ).aggregate(total=Sum('points'))['total'] or 0,
        'achievements': UserAchievement.objects.filter(user=user).count(),
        'badges': UserBadge.objects.filter(user=user).count(),
        'recent_points': PointsTransaction.objects.filter(
            user=user,
            timestamp__date__gte=thirty_days_ago
        ).aggregate(total=Sum('points'))['total'] or 0,
    }
    
    # Learning style if available
    try:
        learning_style = LearningStyle.objects.get(user=user)
        style_data = {
            'primary_style': learning_style.get_primary_style_display(),
            'secondary_style': learning_style.get_secondary_style_display() if learning_style.secondary_style else None,
            'pace': learning_style.get_pace_preference_display(),
            'prefers_group': learning_style.prefers_group_learning,
            'prefers_examples': learning_style.prefers_practical_examples,
            'prefers_theory': learning_style.prefers_theory_first,
            'attention_span': learning_style.attention_span_minutes,
            'confidence': learning_style.confidence_level,
        }
    except LearningStyle.DoesNotExist:
        style_data = None
    
    # Compile all data
    return {
        'user_id': user.id,
        'username': user.username,
        'quiz_performance': quiz_data,
        'courses': courses_data,
        'activity': activity_data,
        'performance': performance_data,
        'gamification': gamification_data,
        'learning_style': style_data,
        'timestamp': timezone.now().isoformat(),
    }


def generate_learning_insights(user, insight_count=3):
    """
    Generate AI-driven learning insights for a user.
    Returns a list of created LearningInsight objects.
    """
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        user_data = get_user_learning_data(user)
        
        # Define the prompt for learning insights
        prompt = f"""Based on this user's learning data, generate {insight_count} insightful observations. 
        For each observation, provide a type, title, and detailed description.
        
        User data: {json.dumps(user_data)}
        
        Format your response as a JSON array with each object containing:
        - insight_type: one of 'learning_pattern', 'engagement', 'performance', 'strength', 'weakness', 'learning_style', 'improvement'
        - title: A concise title for the insight
        - description: A detailed explanation of the insight, including evidence from the data and actionable advice
        - relevance_score: A float between 0 and 1 indicating how confident you are in this insight
        
        Focus on identifying patterns, strengths, weaknesses, and providing actionable advice.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational analytics AI that provides personalized learning insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        # Parse the response
        insights_data = json.loads(response.choices[0].message.content)
        
        # Create the insights
        created_insights = []
        for insight_data in insights_data:
            insight = LearningInsight.objects.create(
                user=user,
                title=insight_data['title'],
                description=insight_data['description'],
                insight_type=insight_data['insight_type'],
                relevance_score=insight_data.get('relevance_score', 0.7)
            )
            created_insights.append(insight)
        
        return created_insights
        
    except Exception as e:
        # Fallback if AI generation fails
        fallback_insight = LearningInsight.objects.create(
            user=user,
            title="Learning Activity Analysis",
            description="Based on your recent activity, we recommend continuing to engage with your courses regularly to maintain your learning momentum.",
            insight_type='recommendation',
            relevance_score=0.5
        )
        
        return [fallback_insight]


def generate_learning_recommendations(user, count=3):
    """
    Generate AI-driven learning recommendations for a user.
    Returns a list of created AILearningRecommendation objects.
    """
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        user_data = get_user_learning_data(user)
        
        # Get courses the user is not enrolled in
        enrolled_course_ids = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
        available_courses = Course.objects.exclude(id__in=enrolled_course_ids)[:5]
        
        # Prepare course data for recommendation
        available_course_data = [
            {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'difficulty': course.difficulty,
            }
            for course in available_courses
        ]
        
        # Define the prompt for recommendations
        prompt = f"""Based on this user's learning data, generate {count} personalized learning recommendations. 
        
        User data: {json.dumps(user_data)}
        
        Available courses: {json.dumps(available_course_data)}
        
        Format your response as a JSON array with each object containing:
        - recommendation_type: one of 'course', 'resource', 'study_technique', 'content_format', 'practice', 'challenge', 'learning_path'
        - title: A concise title for the recommendation
        - description: A detailed explanation of the recommendation, including why it's relevant for this user
        - urgency: 'low', 'medium', or 'high'
        - confidence_score: A float between 0 and 1 indicating your confidence in this recommendation
        - course_id: (optional) The ID of a recommended course from the available courses list
        
        Focus on providing specific, actionable recommendations that address the user's learning style, strengths, weaknesses, and goals.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational recommendation AI that provides personalized learning guidance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        # Parse the response
        recommendations_data = json.loads(response.choices[0].message.content)
        
        # Create the recommendations
        created_recommendations = []
        for rec_data in recommendations_data:
            recommendation = AILearningRecommendation(
                user=user,
                title=rec_data['title'],
                description=rec_data['description'],
                recommendation_type=rec_data['recommendation_type'],
                urgency=rec_data.get('urgency', 'medium'),
                confidence_score=rec_data.get('confidence_score', 0.7),
                # Set expiry date to 30 days from now
                expires_at=timezone.now() + timedelta(days=30)
            )
            
            # Link to course if provided
            if 'course_id' in rec_data and rec_data['recommendation_type'] == 'course':
                try:
                    course = Course.objects.get(id=rec_data['course_id'])
                    recommendation.content_type = ContentType.objects.get_for_model(Course)
                    recommendation.object_id = course.id
                except Course.DoesNotExist:
                    pass
            
            recommendation.save()
            created_recommendations.append(recommendation)
        
        return created_recommendations
        
    except Exception as e:
        # Fallback if AI generation fails
        fallback_recommendation = AILearningRecommendation.objects.create(
            user=user,
            title="Continue Your Learning Journey",
            description="We recommend continuing with your current courses and focusing on completing one module at a time for better retention.",
            recommendation_type='study_technique',
            urgency='medium',
            confidence_score=0.6,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        return [fallback_recommendation]


def detect_learning_style(user):
    """
    Analyze user behavior to detect their learning style and preferences.
    Creates or updates a LearningStyle object for the user.
    """
    # Get activity data
    activities = UserActivity.objects.filter(user=user)
    
    # Initialize counters for different learning modalities
    visual_count = activities.filter(
        Q(activity_type='video_view') | 
        Q(activity_type='image_view')
    ).count()
    
    auditory_count = activities.filter(
        Q(activity_type='audio_view') | 
        Q(activity_type='video_view') # Videos count for both visual and auditory
    ).count()
    
    reading_count = activities.filter(
        Q(activity_type='lesson_view') | 
        Q(activity_type='document_view') |
        Q(activity_type='article_view')
    ).count()
    
    kinesthetic_count = activities.filter(
        Q(activity_type='quiz_attempt') |
        Q(activity_type='interactive_activity')
    ).count()
    
    # Determine primary and secondary learning styles
    modalities = {
        'visual': visual_count,
        'auditory': auditory_count,
        'reading': reading_count,
        'kinesthetic': kinesthetic_count
    }
    
    # If not enough data, return None
    if sum(modalities.values()) < 10:
        return None
    
    # Sort modalities by count
    sorted_modalities = sorted(modalities.items(), key=lambda x: x[1], reverse=True)
    
    primary_style = sorted_modalities[0][0]
    secondary_style = sorted_modalities[1][0] if sorted_modalities[1][1] > 0 else None
    
    # If two modalities are close (within 20%), set as multimodal
    if len(sorted_modalities) >= 2:
        top_count = sorted_modalities[0][1]
        second_count = sorted_modalities[1][1]
        if top_count > 0 and second_count / top_count >= 0.8:
            primary_style = 'multimodal'
            secondary_style = f"{sorted_modalities[0][0]}-{sorted_modalities[1][0]}"
    
    # Analyze pace preference based on time spent
    performance_records = UserPerformance.objects.filter(user=user).order_by('-date')[:30]
    
    if performance_records.exists():
        avg_time_spent = performance_records.aggregate(avg=Avg('time_spent_minutes'))['avg'] or 0
        content_completed = performance_records.aggregate(sum=Sum('content_completed_count'))['sum'] or 0
        
        # Calculate time per content item
        time_per_item = avg_time_spent / max(1, content_completed)
        
        # Determine pace preference
        if time_per_item < 5:
            pace_preference = 'fast'
        elif time_per_item > 15:
            pace_preference = 'slow'
        else:
            pace_preference = 'moderate'
    else:
        pace_preference = 'moderate'  # Default
    
    # Detect group learning preference
    # This could be based on forum participation, group activities, etc.
    # For now, using a placeholder implementation
    prefers_group = activities.filter(
        Q(activity_type='forum_post') | 
        Q(activity_type='comment') |
        Q(activity_type='discussion')
    ).count() > 5
    
    # Create or update learning style
    learning_style, created = LearningStyle.objects.update_or_create(
        user=user,
        defaults={
            'primary_style': primary_style,
            'secondary_style': secondary_style,
            'pace_preference': pace_preference,
            'prefers_group_learning': prefers_group,
            # Default to other preferences for now
            'prefers_practical_examples': True,
            'prefers_theory_first': False,
            'attention_span_minutes': 30,
            'confidence_level': 3  # Moderate confidence
        }
    )
    
    return learning_style 