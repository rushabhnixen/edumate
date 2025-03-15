from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    """
    Course categories (e.g., Programming, Business, Design).
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(_('Icon Class'), max_length=50, blank=True, help_text=_('Font Awesome icon class'))
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('courses:category_detail', args=[self.slug])
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """
    Main course model containing general information.
    """
    DIFFICULTY_CHOICES = (
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField(blank=True)
    description = models.TextField()
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_created'
    )
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='courses',
        null=True,
        blank=True
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner'
    )
    prerequisites = models.TextField(blank=True)
    learning_outcomes = models.TextField(_('Learning Outcomes'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='courses_enrolled',
        blank=True,
        through='Enrollment'
    )
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('courses:course_detail', args=[self.slug])
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def total_modules(self):
        return self.modules.count()
    
    @property
    def total_students(self):
        return self.students.count()
    
    @property
    def rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0


class Module(models.Model):
    """
    Course modules containing lessons and activities.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('Module')
        verbose_name_plural = _('Modules')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Content(models.Model):
    """
    Abstract base model for different types of content.
    """
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='contents',
        verbose_name=_('Module')
    )
    title = models.CharField(_('Title'), max_length=200)
    order = models.PositiveIntegerField(_('Order'), default=0)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['order']


class Lesson(Content):
    """
    Text-based lesson content.
    """
    content = models.TextField(_('Content'))
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
    
    def __str__(self):
        return self.title


class Video(Content):
    """
    Video lesson content.
    """
    url = models.URLField(_('Video URL'))
    duration = models.PositiveIntegerField(_('Duration (seconds)'), default=0)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='videos')
    
    class Meta:
        verbose_name = _('Video')
        verbose_name_plural = _('Videos')
    
    def __str__(self):
        return self.title


class Quiz(Content):
    """
    Quiz content for assessment.
    """
    description = models.TextField(_('Description'))
    time_limit = models.PositiveIntegerField(_('Time Limit (minutes)'), default=30)
    passing_score = models.PositiveIntegerField(_('Passing Score (%)'), default=70)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes')
    
    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')
    
    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Quiz questions.
    """
    QUESTION_TYPES = (
        ('multiple_choice', _('Multiple Choice')),
        ('true_false', _('True/False')),
        ('short_answer', _('Short Answer')),
    )
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.TextField(_('Question Text'))
    question_type = models.CharField(
        _('Question Type'),
        max_length=20,
        choices=QUESTION_TYPES,
        default='multiple_choice'
    )
    points = models.PositiveIntegerField(_('Points'), default=1)
    order = models.PositiveIntegerField(_('Order'), default=0)
    explanation = models.TextField(
        blank=True,
        help_text=_("Explanation to show after answering")
    )
    
    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"


class Answer(models.Model):
    """
    Possible answers for quiz questions.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Question')
    )
    text = models.CharField(_('Answer Text'), max_length=255)
    is_correct = models.BooleanField(_('Correct Answer'), default=False)
    
    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
    
    def __str__(self):
        return f"{self.question.text[:30]}... - {self.text[:30]}..."


class Enrollment(models.Model):
    """
    Track student enrollments in courses.
    """
    STATUS_CHOICES = (
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    )
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = [['student', 'course']]
        
    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"
    
    def save(self, *args, **kwargs):
        # Set completed_at when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class Progress(models.Model):
    """
    Tracking student progress through course content.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    completed_lessons = models.ManyToManyField(
        Lesson,
        blank=True,
        related_name='completed_by'
    )
    completed_videos = models.ManyToManyField(
        Video,
        related_name='completed_by',
        verbose_name=_('Completed Videos'),
        blank=True
    )
    completed_quizzes = models.ManyToManyField(
        Quiz,
        blank=True,
        related_name='completed_by'
    )
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Progress')
        verbose_name_plural = _('Progress')
        unique_together = ('student', 'course', 'module')
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.module.title}"
    
    @property
    def completion_percentage(self):
        """Calculate the completion percentage for this module."""
        total_items = self.module.lessons.count() + self.module.quizzes.count()
        if total_items == 0:
            return 0
        
        completed_items = self.completed_lessons.count() + self.completed_quizzes.count()
        return (completed_items / total_items) * 100


class QuizAttempt(models.Model):
    """
    Student attempts at quizzes.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Quiz Attempt')
        verbose_name_plural = _('Quiz Attempts')
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"
    
    @property
    def score_percentage(self):
        if self.max_score == 0:
            return 0
        return (self.score / self.max_score) * 100


class PersonalizedQuizAttempt(models.Model):
    """
    Model to store attempts at personalized quizzes.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='personalized_quiz_attempts'
    )
    title = models.CharField(max_length=200)
    score = models.FloatField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Personalized Quiz Attempt')
        verbose_name_plural = _('Personalized Quiz Attempts')
    
    def __str__(self):
        return f"{self.user.username} - {self.title} - {self.created_at.strftime('%Y-%m-%d')}"


class Option(models.Model):
    """
    Options for quiz questions.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options'
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Option')
        verbose_name_plural = _('Options')
    
    def __str__(self):
        return f"{self.question.text[:30]}... - {self.text[:30]}..." 