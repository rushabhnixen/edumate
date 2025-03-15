from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm

from .models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users with our custom fields.
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    is_student = forms.BooleanField(required=False, initial=True, help_text=_("Register as a student"))
    is_instructor = forms.BooleanField(required=False, help_text=_("Register as an instructor"))
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_instructor')


class CustomUserChangeForm(UserChangeForm):
    """
    Form for updating users with our custom fields.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture', 
                  'date_of_birth')


class CustomSignupForm(SignupForm):
    """
    Custom signup form for django-allauth.
    """
    first_name = forms.CharField(max_length=30, label=_('First Name'))
    last_name = forms.CharField(max_length=30, label=_('Last Name'))
    is_student = forms.BooleanField(required=False, initial=True, label=_('I am a student'))
    is_instructor = forms.BooleanField(required=False, label=_('I am an instructor'))
    
    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_student = self.cleaned_data.get('is_student', True)
        user.is_instructor = self.cleaned_data.get('is_instructor', False)
        user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information.
    """
    class Meta:
        model = UserProfile
        fields = [
            'location', 
            'website', 
            'social_links', 
            'interests',
            'content_difficulty_preference',
            'email_notifications',
            'achievement_notifications',
            'reminder_notifications'
        ]
        widgets = {
            'social_links': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter as JSON: {"twitter": "username", "linkedin": "url"}'}),
            'interests': forms.TextInput(attrs={'placeholder': 'e.g., Programming, Data Science, Design'}),
        }


class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration.
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(user=user)
        
        return user


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating user information.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture', 
                 'date_of_birth', 'bio', 'learning_style']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'learning_style': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    """
    class Meta:
        model = UserProfile
        fields = ['location', 'website', 'interests', 'content_difficulty_preference',
                 'email_notifications', 'achievement_notifications', 'reminder_notifications']
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'interests': forms.TextInput(attrs={'class': 'form-control'}),
            'content_difficulty_preference': forms.Select(attrs={'class': 'form-select'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'achievement_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 