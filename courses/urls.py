from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course list and detail views
    path('', views.CourseListView.as_view(), name='course_list'),
    path('category/<slug:category_slug>/', views.CourseListView.as_view(), name='category_detail'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='detail'),
    path('<slug:slug>/enroll/', views.enroll_course, name='enroll'),
    
    # Course content views
    path('<slug:slug>/modules/', views.ModuleListView.as_view(), name='module_list'),
    path('<slug:course_slug>/modules/<int:module_id>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('<slug:course_slug>/modules/<int:module_id>/complete/', views.complete_module, name='complete_module'),
    
    # Lesson and content views
    path('<slug:course_slug>/lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('<slug:course_slug>/videos/<int:video_id>/', views.video_detail, name='video_detail'),
    
    # Quiz views
    path('<slug:course_slug>/quizzes/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('<slug:course_slug>/quizzes/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('<slug:course_slug>/quizzes/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('<slug:course_slug>/quizzes/<int:quiz_id>/results/', views.quiz_results, name='quiz_results'),
    path('<slug:course_slug>/quizzes/<int:quiz_id>/results/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    
    # Personalized quiz views
    path('personalized-quiz/', views.generate_personalized_quiz, name='generate_personalized_quiz'),
    path('personalized-quiz/<int:quiz_id>/', views.take_personalized_quiz, name='take_personalized_quiz'),
    path('personalized-quiz/<int:quiz_id>/results/', views.personalized_quiz_results, name='personalized_quiz_results'),
    
    # Student course management
    path('my-courses/', views.my_courses, name='my_courses'),
    path('<slug:slug>/content/', views.course_content, name='course_content'),
    
    # Instructor course management
    path('create/', views.CourseCreateView.as_view(), name='create'),
] 