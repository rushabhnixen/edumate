from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('insights/', views.learning_insights, name='learning_insights'),
    path('insights/generate/', views.generate_insight, name='generate_insight'),
    path('rate-difficulty/', views.rate_content_difficulty, name='rate_difficulty'),
    path('instructor-dashboard/', views.InstructorDashboardView.as_view(), name='instructor_dashboard'),
    path('course-analytics/<slug:slug>/', views.CourseAnalyticsView.as_view(), name='course_analytics'),
    path('log-activity/', views.log_activity, name='log_activity'),
    path('dashboard/student/', views.student_analytics_dashboard, name='student_dashboard'),
    path('dashboard/instructor/', views.instructor_analytics_dashboard, name='instructor_dashboard'),
] 