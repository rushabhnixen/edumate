from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType

from .models import (
    Category, Course, Module, Lesson, Video, Quiz,
    Question, Option, Answer, Enrollment, Progress, QuizAttempt,
    PersonalizedQuizAttempt
)
from gamification.models import Point, Achievement, UserAchievement
from .forms import CourseForm, ModuleForm, LessonForm, QuizForm, QuestionForm
from accounts.models import CustomUser, UserActivity


class CourseListView(ListView):
    """
    Display a list of all published courses.
    """
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_published=True)
        
        # Filter by category if provided
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by search query if provided
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(overview__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by difficulty if provided
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.kwargs.get('category_slug')
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_difficulty'] = self.request.GET.get('difficulty', '')
        return context


class CourseDetailView(DetailView):
    """
    Display details of a specific course.
    """
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Check if user is enrolled
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                course=course
            ).exists()
        else:
            context['is_enrolled'] = False
        
        # Get course modules and their content counts
        modules = course.modules.all().annotate(
            lesson_count=Count('contents', filter=Q(contents__lesson__isnull=False)),
            video_count=Count('contents', filter=Q(contents__video__isnull=False)),
            quiz_count=Count('contents', filter=Q(contents__quiz__isnull=False))
        )
        context['modules'] = modules
        
        # Get total content count
        context['total_lessons'] = sum(m.lesson_count for m in modules)
        context['total_videos'] = sum(m.video_count for m in modules)
        context['total_quizzes'] = sum(m.quiz_count for m in modules)
        
        return context


@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    # Check if user is already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, f"You are already enrolled in {course.title}")
        return redirect('courses:detail', slug=slug)
    
    # Check if user is the instructor
    if request.user == course.instructor:
        messages.warning(request, "You cannot enroll in your own course")
        return redirect('courses:detail', slug=slug)
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        student=request.user,
        course=course,
        status='enrolled'
    )
    
    # Award points for enrolling
    Point.objects.create(
        user=request.user,
        points=10,  # Adjust point value as needed
        description=f"Enrolled in course: {course.title}"
    )
    
    # Record user activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='course_view',
        content_type=ContentType.objects.get_for_model(course),
        object_id=course.id
    )
    
    # Check for first enrollment achievement
    enrollment_count = Enrollment.objects.filter(student=request.user).count()
    if enrollment_count == 1:
        try:
            achievement = Achievement.objects.get(name="First Course Enrollment")
            UserAchievement.objects.get_or_create(
                user=request.user,
                achievement=achievement
            )
        except Achievement.DoesNotExist:
            pass  # Achievement doesn't exist yet
    
    messages.success(request, f"You have successfully enrolled in {course.title}! You earned 10 points.")
    return redirect('courses:module_list', slug=slug)


@login_required
def my_courses(request):
    """
    Display courses the user is enrolled in.
    """
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    
    # Calculate progress for each course
    for enrollment in enrollments:
        course = enrollment.course
        progress_records = Progress.objects.filter(
            student=request.user,
            course=course
        )
        
        if progress_records.exists():
            total_percentage = sum(p.completion_percentage for p in progress_records)
            enrollment.overall_progress = total_percentage / progress_records.count()
        else:
            enrollment.overall_progress = 0
    
    context = {
        'enrollments': enrollments
    }
    
    return render(request, 'courses/my_courses.html', context)


@login_required
def course_content(request, slug):
    """
    Display course content for enrolled students.
    """
    course = get_object_or_404(Course, slug=slug)
    
    # Check if user is enrolled
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Get all modules with their content
    modules = course.modules.all().prefetch_related('contents')
    
    # Get progress for each module
    progress_records = Progress.objects.filter(
        student=request.user,
        course=course
    )
    
    # Create a dictionary of module_id -> progress
    progress_dict = {p.module_id: p for p in progress_records}
    
    context = {
        'course': course,
        'modules': modules,
        'enrollment': enrollment,
        'progress_dict': progress_dict
    }
    
    return render(request, 'courses/course_content.html', context)


@login_required
def lesson_detail(request, course_slug, lesson_id):
    """
    Display a specific lesson.
    """
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    
    # Check if user is enrolled
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Get progress record for this module
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        course=course,
        module=lesson.module
    )
    
    # Mark lesson as completed if not already
    if request.method == 'POST' and 'mark_completed' in request.POST:
        if lesson not in progress.completed_lessons.all():
            progress.completed_lessons.add(lesson)
            
            # Add points for completing a lesson (gamification)
            request.user.points += 10
            request.user.save()
            
            messages.success(request, f"Lesson marked as completed. +10 points!")
        
        return redirect('courses:lesson_detail', course_slug=course_slug, lesson_id=lesson_id)
    
    context = {
        'course': course,
        'lesson': lesson,
        'enrollment': enrollment,
        'progress': progress,
        'is_completed': lesson in progress.completed_lessons.all()
    }
    
    return render(request, 'courses/lesson_detail.html', context)


@login_required
def video_detail(request, course_slug, video_id):
    """
    Display a specific video.
    """
    course = get_object_or_404(Course, slug=course_slug)
    video = get_object_or_404(Video, id=video_id, module__course=course)
    
    # Check if user is enrolled
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Get progress record for this module
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        course=course,
        module=video.module
    )
    
    # Mark video as completed if not already
    if request.method == 'POST' and 'mark_completed' in request.POST:
        if video not in progress.completed_videos.all():
            progress.completed_videos.add(video)
            
            # Add points for completing a video (gamification)
            request.user.points += 15
            request.user.save()
            
            messages.success(request, f"Video marked as completed. +15 points!")
        
        return redirect('courses:video_detail', course_slug=course_slug, video_id=video_id)
    
    context = {
        'course': course,
        'video': video,
        'enrollment': enrollment,
        'progress': progress,
        'is_completed': video in progress.completed_videos.all()
    }
    
    return render(request, 'courses/video_detail.html', context)


@login_required
def quiz_detail(request, course_slug, quiz_id):
    """
    Display a specific quiz.
    """
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course=course)
    
    # Check if user is enrolled
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    
    # Get progress record for this module
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        course=course,
        module=quiz.module
    )
    
    # Check if quiz is already completed
    is_completed = quiz in progress.completed_quizzes.all()
    
    # Get previous attempts
    previous_attempts = QuizAttempt.objects.filter(
        student=request.user,
        quiz=quiz
    ).order_by('-started_at')
    
    context = {
        'course': course,
        'quiz': quiz,
        'enrollment': enrollment,
        'progress': progress,
        'is_completed': is_completed,
        'previous_attempts': previous_attempts,
        'questions': quiz.questions.all().prefetch_related('answers')
    }
    
    return render(request, 'courses/quiz_detail.html', context)


@login_required
def submit_quiz(request, course_slug, quiz_id):
    """
    Process quiz submission and calculate score.
    """
    if request.method != 'POST':
        return redirect('courses:quiz_detail', course_slug=course_slug, quiz_id=quiz_id)
    
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course=course)
    
    # Get all questions for this quiz
    questions = quiz.questions.all()
    
    # Calculate score
    score = 0
    max_score = sum(q.points for q in questions)
    
    for question in questions:
        # Get the submitted answer(s)
        if question.question_type == 'multiple_choice':
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                answer = get_object_or_404(Answer, id=answer_id, question=question)
                if answer.is_correct:
                    score += question.points
        elif question.question_type == 'true_false':
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                answer = get_object_or_404(Answer, id=answer_id, question=question)
                if answer.is_correct:
                    score += question.points
        elif question.question_type == 'short_answer':
            # For short answer, we'll need to implement more sophisticated checking
            # This is a simplified version
            user_answer = request.POST.get(f'question_{question.id}', '').strip().lower()
            correct_answers = [a.text.strip().lower() for a in question.answers.filter(is_correct=True)]
            if user_answer in correct_answers:
                score += question.points
    
    # Calculate percentage score
    percentage_score = (score / max_score * 100) if max_score > 0 else 0
    
    # Determine if passed
    passed = percentage_score >= quiz.passing_score
    
    # Create quiz attempt record
    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        score=score,
        max_score=max_score,
        completed_at=timezone.now(),
        passed=passed
    )
    
    # If passed, mark quiz as completed in progress
    if passed:
        progress = get_object_or_404(Progress, student=request.user, course=course, module=quiz.module)
        progress.completed_quizzes.add(quiz)
        
        # Add points for completing a quiz (gamification)
        points_earned = 25 + int(percentage_score / 4)  # Base points + bonus based on score
        request.user.points += points_earned
        request.user.save()
        
        messages.success(request, f"Quiz completed successfully! You earned {points_earned} points!")
    else:
        messages.warning(request, f"You didn't pass the quiz. Required: {quiz.passing_score}%, Your score: {int(percentage_score)}%")
    
    return redirect('courses:quiz_result', course_slug=course_slug, quiz_id=quiz_id, attempt_id=attempt.id)


@login_required
def quiz_result(request, course_slug, quiz_id, attempt_id):
    """
    Display quiz results.
    """
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id, module__course=course)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user, quiz=quiz)
    
    context = {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'score_percentage': attempt.score_percentage,
        'passed': attempt.passed
    }
    
    return render(request, 'courses/quiz_result.html', context)


@login_required
def generate_personalized_quiz(request, course_id=None):
    """
    Generate a personalized quiz based on user's weak areas.
    """
    user = request.user
    
    if not user.is_student:
        messages.error(request, "Only students can access personalized quizzes.")
        return redirect('accounts:dashboard')
    
    # Get user's quiz attempts to identify weak areas
    quiz_attempts = QuizAttempt.objects.filter(student=user)
    
    # If no quiz attempts, redirect to regular quizzes
    if not quiz_attempts.exists():
        messages.info(request, "Complete some quizzes first to get personalized challenges.")
        if course_id:
            return redirect('courses:course_detail', slug=Course.objects.get(id=course_id).slug)
        return redirect('courses:course_list')
    
    # Identify weak topics based on quiz performance
    weak_topics = []
    for attempt in quiz_attempts:
        if attempt.score < 70:  # Consider topics with score below 70% as weak
            weak_topics.append(attempt.quiz.lesson.id)
    
    # If no weak topics found, use topics with lowest scores
    if not weak_topics:
        lowest_score_attempts = quiz_attempts.order_by('score')[:3]
        weak_topics = [attempt.quiz.lesson.id for attempt in lowest_score_attempts]
    
    # Get questions from weak topics
    questions = []
    if course_id:
        # If course_id is provided, get questions only from that course
        questions = Question.objects.filter(
            quiz__lesson__module__course_id=course_id,
            quiz__lesson__id__in=weak_topics
        ).order_by('?')[:10]  # Randomly select 10 questions
    else:
        # Otherwise, get questions from all weak topics
        questions = Question.objects.filter(
            quiz__lesson__id__in=weak_topics
        ).order_by('?')[:10]  # Randomly select 10 questions
    
    # If not enough questions found, get random questions
    if questions.count() < 5:
        if course_id:
            additional_questions = Question.objects.filter(
                quiz__lesson__module__course_id=course_id
            ).exclude(id__in=[q.id for q in questions]).order_by('?')[:10-questions.count()]
            questions = list(questions) + list(additional_questions)
        else:
            additional_questions = Question.objects.all().exclude(
                id__in=[q.id for q in questions]
            ).order_by('?')[:10-questions.count()]
            questions = list(questions) + list(additional_questions)
    
    # Create a temporary quiz in session
    request.session['personalized_quiz'] = {
        'title': 'Personalized Challenge',
        'description': 'This quiz is tailored to help you improve in areas where you need practice.',
        'questions': [
            {
                'id': q.id,
                'text': q.text,
                'options': [
                    {'id': o.id, 'text': o.text} 
                    for o in q.option_set.all()
                ]
            } 
            for q in questions
        ]
    }
    
    return redirect('courses:take_personalized_quiz')


@login_required
def take_personalized_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Record user activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='personalized_quiz_attempt',
        content_object=quiz
    )
    
    if request.method == 'POST':
        # Process quiz submission
        score = 0
        correct_answers = 0
        total_questions = quiz.questions.count()
        
        for question in quiz.questions.all():
            # Get user's answer
            if question.question_type == 'multiple_choice':
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    selected_option = get_object_or_404(Option, id=answer_id)
                    if selected_option.is_correct:
                        score += question.points
                        correct_answers += 1
            elif question.question_type == 'true_false':
                answer = request.POST.get(f'question_{question.id}')
                correct_answer = question.options.filter(is_correct=True).first()
                if answer and correct_answer and answer == str(correct_answer.id):
                    score += question.points
                    correct_answers += 1
            elif question.question_type == 'short_answer':
                user_answer = request.POST.get(f'question_{question.id}', '').strip().lower()
                correct_option = question.options.filter(is_correct=True).first()
                if correct_option and user_answer == correct_option.text.strip().lower():
                    score += question.points
                    correct_answers += 1
        
        # Create personalized quiz attempt record
        attempt = PersonalizedQuizAttempt.objects.create(
            user=request.user,
            title=f"Personalized Quiz: {quiz.title}",
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers
        )
        
        # Award points for completing personalized quiz
        Point.objects.create(
            user=request.user,
            points=15,  # Adjust point value as needed
            description=f"Completed personalized quiz: {quiz.title}"
        )
        
        # Check for achievements
        personalized_quizzes_taken = PersonalizedQuizAttempt.objects.filter(
            user=request.user
        ).count()
        
        # Example: Award achievement for taking first personalized quiz
        if personalized_quizzes_taken == 1:
            try:
                achievement = Achievement.objects.get(name="First Personalized Quiz")
                UserAchievement.objects.get_or_create(
                    user=request.user,
                    achievement=achievement
                )
            except Achievement.DoesNotExist:
                pass  # Achievement doesn't exist yet
        
        return redirect('courses:personalized_quiz_results', quiz_id=quiz_id)
    
    # Display quiz
    context = {
        'quiz': quiz,
        'questions': quiz.questions.all().order_by('?')[:10],  # Randomize and limit to 10 questions
        'time_limit_seconds': 15 * 60,  # 15 minutes for personalized quiz
    }
    
    return render(request, 'courses/take_personalized_quiz.html', context)


@login_required
def personalized_quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Get the latest attempt
    attempt = PersonalizedQuizAttempt.objects.filter(
        user=request.user,
        title__contains=quiz.title
    ).order_by('-created_at').first()
    
    if not attempt:
        messages.warning(request, "You haven't taken this personalized quiz yet")
        return redirect('courses:take_personalized_quiz', quiz_id=quiz_id)
    
    # Calculate percentage score
    percentage_score = (attempt.correct_answers / attempt.total_questions * 100) if attempt.total_questions > 0 else 0
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'percentage_score': percentage_score,
        'passed': percentage_score >= 70,  # Assuming 70% is passing
    }
    
    return render(request, 'courses/personalized_quiz_results.html', context)


@login_required
def quiz_results(request, course_slug, quiz_id):
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Get the latest attempt
    attempt = QuizAttempt.objects.filter(
        student=request.user,
        quiz=quiz
    ).order_by('-completed_at').first()
    
    if not attempt:
        messages.warning(request, "You haven't taken this quiz yet")
        return redirect('courses:take_quiz', course_slug=course_slug, quiz_id=quiz_id)
    
    context = {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'percentage_score': (attempt.score / attempt.max_score * 100) if attempt.max_score > 0 else 0,
        'module': quiz.module,
    }
    
    return render(request, 'courses/quiz_results.html', context)


class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def test_func(self):
        return self.request.user.is_instructor
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        form.instance.slug = slugify(form.instance.title)
        messages.success(self.request, f'Course "{form.instance.title}" has been created!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('courses:detail', kwargs={'slug': self.object.slug})


class ModuleListView(LoginRequiredMixin, ListView):
    model = Module
    template_name = 'courses/module_list.html'
    context_object_name = 'modules'
    
    def get_queryset(self):
        self.course = get_object_or_404(Course, slug=self.kwargs['slug'])
        return Module.objects.filter(course=self.course).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context


class ModuleDetailView(LoginRequiredMixin, DetailView):
    model = Module
    template_name = 'courses/module_detail.html'
    context_object_name = 'module'
    
    def get_object(self):
        course_slug = self.kwargs.get('course_slug')
        module_id = self.kwargs.get('module_id')
        course = get_object_or_404(Course, slug=course_slug)
        return get_object_or_404(Module, course=course, id=module_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        context['lessons'] = self.object.lessons.all().order_by('order')
        context['quizzes'] = self.object.quizzes.all()
        
        # Get previous and next modules
        all_modules = list(Module.objects.filter(course=self.object.course).order_by('order'))
        current_index = all_modules.index(self.object)
        
        if current_index > 0:
            context['prev_module'] = all_modules[current_index - 1]
        if current_index < len(all_modules) - 1:
            context['next_module'] = all_modules[current_index + 1]
        
        # Check if user has completed this module
        if self.request.user.is_authenticated:
            progress, created = Progress.objects.get_or_create(
                student=self.request.user,
                course=self.object.course,
                module=self.object
            )
            context['progress'] = progress
            
            # Record user activity
            UserActivity.objects.create(
                user=self.request.user,
                activity_type='module_view',
                content_object=self.object
            )
        
        return context 


@login_required
def complete_module(request, course_slug, module_id):
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Get or create progress record
    progress, created = Progress.objects.get_or_create(
        student=request.user,
        course=course,
        module=module
    )
    
    # Check if all lessons and quizzes are completed
    lessons = module.lessons.all()
    quizzes = module.quizzes.all()
    
    all_completed = True
    
    # Check lessons
    for lesson in lessons:
        if lesson not in progress.completed_lessons.all():
            all_completed = False
            break
    
    # Check quizzes
    if all_completed:
        for quiz in quizzes:
            if quiz not in progress.completed_quizzes.all():
                all_completed = False
                break
    
    if all_completed:
        # Award points for completing the module
        Point.objects.create(
            user=request.user,
            points=50,  # Adjust point value as needed
            description=f"Completed module: {module.title}"
        )
        
        # Check for achievements
        modules_completed = Progress.objects.filter(
            student=request.user,
            completion_percentage=100
        ).count()
        
        # Example: Award achievement for completing first module
        if modules_completed == 1:
            achievement = Achievement.objects.get(name="First Module Completed")
            UserAchievement.objects.get_or_create(
                user=request.user,
                achievement=achievement
            )
        
        messages.success(request, f"Congratulations! You've completed the module '{module.title}' and earned 50 points!")
    else:
        messages.warning(request, "You need to complete all lessons and quizzes to mark this module as complete.")
    
    return redirect('courses:module_detail', course_slug=course_slug, module_id=module_id)


@login_required
def take_quiz(request, course_slug, quiz_id):
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.warning(request, "You must be enrolled in this course to take the quiz")
        return redirect('courses:detail', slug=course_slug)
    
    # Check if quiz belongs to the course
    if quiz.module.course != course:
        messages.error(request, "Invalid quiz for this course")
        return redirect('courses:detail', slug=course_slug)
    
    # Record user activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='quiz_attempt',
        content_object=quiz
    )
    
    if request.method == 'POST':
        # Process quiz submission
        score = 0
        max_score = 0
        
        for question in quiz.questions.all():
            max_score += question.points
            
            # Get user's answer
            if question.question_type == 'multiple_choice':
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    selected_option = get_object_or_404(Option, id=answer_id)
                    if selected_option.is_correct:
                        score += question.points
            elif question.question_type == 'true_false':
                answer = request.POST.get(f'question_{question.id}')
                correct_answer = question.options.filter(is_correct=True).first()
                if answer and correct_answer and answer == str(correct_answer.id):
                    score += question.points
            elif question.question_type == 'short_answer':
                # For short answer, we'll need a more sophisticated checking mechanism
                # This is a simplified version
                user_answer = request.POST.get(f'question_{question.id}', '').strip().lower()
                correct_option = question.options.filter(is_correct=True).first()
                if correct_option and user_answer == correct_option.text.strip().lower():
                    score += question.points
        
        # Calculate percentage score
        percentage_score = (score / max_score * 100) if max_score > 0 else 0
        passed = percentage_score >= quiz.passing_score
        
        # Create quiz attempt record
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=score,
            max_score=max_score,
            passed=passed,
            completed_at=timezone.now()
        )
        
        # If passed, update progress
        if passed:
            progress, created = Progress.objects.get_or_create(
                student=request.user,
                course=course,
                module=quiz.module
            )
            progress.completed_quizzes.add(quiz)
            
            # Award points for passing quiz
            Point.objects.create(
                user=request.user,
                points=20,  # Adjust point value as needed
                description=f"Passed quiz: {quiz.title}"
            )
            
            # Check for achievements
            quizzes_passed = QuizAttempt.objects.filter(
                student=request.user,
                passed=True
            ).count()
            
            # Example: Award achievement for passing first quiz
            if quizzes_passed == 1:
                try:
                    achievement = Achievement.objects.get(name="First Quiz Passed")
                    UserAchievement.objects.get_or_create(
                        user=request.user,
                        achievement=achievement
                    )
                except Achievement.DoesNotExist:
                    pass  # Achievement doesn't exist yet
        
        return redirect('courses:quiz_results', course_slug=course_slug, quiz_id=quiz_id)
    
    # Display quiz
    context = {
        'course': course,
        'quiz': quiz,
        'questions': quiz.questions.all().order_by('order'),
        'time_limit_seconds': quiz.time_limit * 60,
    }
    
    return render(request, 'courses/take_quiz.html', context) 