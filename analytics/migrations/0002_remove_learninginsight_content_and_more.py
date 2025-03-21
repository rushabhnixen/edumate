# Generated by Django 4.2.7 on 2025-03-15 17:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learninginsight',
            name='content',
        ),
        migrations.RemoveField(
            model_name='learninginsight',
            name='relevance_score',
        ),
        migrations.RemoveField(
            model_name='useractivity',
            name='details',
        ),
        migrations.AddField(
            model_name='learninginsight',
            name='description',
            field=models.TextField(blank=True, default='No description provided'),
        ),
        migrations.AddField(
            model_name='learninginsight',
            name='title',
            field=models.CharField(default='Learning Insight', max_length=255),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='analytics_activities', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='referrer',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='session_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='user_agent',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='learninginsight',
            name='generated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='learninginsight',
            name='insight_type',
            field=models.CharField(choices=[('learning_pattern', 'Learning Pattern'), ('engagement', 'Engagement'), ('performance', 'Performance'), ('recommendation', 'Recommendation'), ('study_habit', 'Study Habit')], max_length=50),
        ),
        migrations.AlterField(
            model_name='learninginsight',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='learninginsight',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_insights', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='useractivity',
            name='activity_type',
            field=models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'), ('page_view', 'Page View'), ('course_view', 'Course View'), ('lesson_view', 'Lesson View'), ('quiz_attempt', 'Quiz Attempt'), ('search', 'Search'), ('download', 'Download'), ('comment', 'Comment'), ('rating', 'Rating')], max_length=50),
        ),
        migrations.AlterField(
            model_name='useractivity',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='useractivity',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analytics_activities', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='UserEngagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('time_spent', models.PositiveIntegerField(help_text='Time spent in seconds')),
                ('pages_visited', models.PositiveIntegerField(default=0)),
                ('lessons_completed', models.PositiveIntegerField(default=0)),
                ('quizzes_taken', models.PositiveIntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='engagement_metrics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Engagement',
                'verbose_name_plural': 'User Engagements',
                'ordering': ['-date'],
                'unique_together': {('user', 'date')},
            },
        ),
    ]
