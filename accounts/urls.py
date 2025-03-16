from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Password management
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change_form.html',
        success_url='/accounts/password-change/done/'
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    
    # User profile and dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),
    
    # Student specific views
    path('become-student/', views.become_student, name='become_student'),
    
    # Instructor specific views
    path('become-instructor/', views.become_instructor, name='become_instructor'),
] 