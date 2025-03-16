from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Student-facing URLs
    path('', views.CourseListView.as_view(), name='course_list'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('enroll/<slug:slug>/', views.enroll_course, name='enroll_course'),
    path('content/<slug:slug>/', views.course_content, name='course_content'),
    path('content/view/<int:content_id>/', views.view_content, name='view_content'),
    path('quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('quiz/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    path('quiz/result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    
    # Instructor-facing URLs
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/courses/', views.instructor_courses, name='instructor_courses'),
    path('instructor/course/create/', views.CourseCreateView.as_view(), name='create_course'),
    path('instructor/course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('instructor/course/<int:course_id>/modules/', views.edit_course_modules, name='edit_course_modules'),
    path('instructor/course/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('instructor/module/<int:module_id>/content/', views.module_content_list, name='module_content_list'),
    path('instructor/module/<int:module_id>/content/add/', views.add_module_content, name='add_module_content'),
    path('instructor/content/<int:content_id>/quiz/create/', views.create_quiz, name='create_quiz'),
    path('instructor/quiz/<int:quiz_id>/questions/', views.add_quiz_questions, name='add_quiz_questions'),
    path('instructor/quiz/<int:quiz_id>/questions/list/', views.quiz_questions_list, name='quiz_questions_list'),
    path('instructor/question/<int:question_id>/answers/', views.add_question_answers, name='add_question_answers'),

    # Add the study planner URL pattern
    path('study-planner/', views.study_planner, name='study_planner'),
    path('study-planner/add-session/', views.add_study_session, name='add_study_session'),
    path('study-planner/update-session/<int:session_id>/', views.update_study_session, name='update_study_session'),
    path('study-planner/delete-session/<int:session_id>/', views.delete_study_session, name='delete_study_session'),
    path('study-planner/update-preferences/', views.update_study_preferences, name='update_study_preferences'),
    path('study-planner/add-deadline/', views.add_deadline, name='add_deadline'),
    path('study-planner/update-deadline/<int:deadline_id>/', views.update_deadline, name='update_deadline'),
    path('study-planner/delete-deadline/<int:deadline_id>/', views.delete_deadline, name='delete_deadline'),
    path('study-planner/add-focus-area/', views.add_focus_area, name='add_focus_area'),
    path('study-planner/update-focus-area/<int:focus_area_id>/', views.update_focus_area, name='update_focus_area'),
    path('study-planner/delete-focus-area/<int:focus_area_id>/', views.delete_focus_area, name='delete_focus_area'),
    path('study-planner/add-goal/', views.add_study_goal, name='add_study_goal'),
    path('study-planner/update-goal/<int:goal_id>/', views.update_study_goal, name='update_study_goal'),
    path('study-planner/delete-goal/<int:goal_id>/', views.delete_study_goal, name='delete_study_goal'),

    # Add the personalized recommendations URL pattern
    path('personalized-recommendations/', views.personalized_recommendations, name='personalized_recommendations'),

    # Add the learning path URL pattern
    path('learning-path/', views.learning_path, name='learning_path'),

    # Add this line in your urlpatterns list
    path('course/<slug:slug>/modules/', views.ModuleListView.as_view(), name='module_list'),
] 