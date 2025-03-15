from django import forms
from django.forms import inlineformset_factory
from .models import Course, Module, Lesson, Quiz, Question, Option, Category

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'category', 'difficulty', 
            'thumbnail', 'prerequisites', 'is_published'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'prerequisites': forms.Textarea(attrs={'rows': 3}),
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'rich-text-editor'}),
        }

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'passing_score']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'explanation', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
        }

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Create a formset for options
OptionFormSet = inlineformset_factory(
    Question, 
    Option,
    form=OptionForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True
) 