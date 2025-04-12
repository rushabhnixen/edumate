# EduMate - Learn, Play, Achieve!

EduMate is a gamified EdTech web application designed to enhance learning engagement and retention through AI-driven personalization and game mechanics. The platform addresses the challenges of passive learning by integrating elements such as points, badges, leaderboards, and adaptive learning insights, ensuring a highly interactive and motivating educational experience.

## Features

- **AI-Powered Personalization:** Adapts content difficulty based on learner performance and engagement.
- **Dynamic Challenges & Rewards:** Provides interactive challenges and rewards for progress.
- **Leaderboard & Social Engagement:** Encourages competition and collaboration among learners.
- **Real-Time Feedback:** Offers instant AI-generated insights to guide learners effectively.
- **Gamified Learning Modules:** Incorporates quizzes, missions, and streak tracking to sustain motivation.
- **Learning Analytics Dashboard:** Enables tracking of user progress, strengths, and improvement areas.
- **Study Planner:** Helps students organize their study sessions and track their progress.

## Technology Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, Bootstrap, JavaScript
- **Database:** PostgreSQL (SQLite for development)
- **AI/ML Integration:** Deepseek, ChatGPT

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/edumate.git
   cd edumate
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Start the development server:
   ```
   python manage.py runserver
   ```

7. Access the application at http://localhost:8000/

## Usage

### For Instructors

1. Log in with your instructor account.
2. Create courses, modules, and content.
3. Add quizzes and questions to assess student knowledge.
4. Monitor student progress through the instructor dashboard.

### For Students

1. Browse available courses and enroll.
2. Access course content and take quizzes.
3. Track your progress through the learning path.
4. Use the study planner to organize your study sessions.
5. Get personalized recommendations based on your performance.

## Project Structure

- `accounts/` - User authentication and profile management
- `courses/` - Course content and learning modules
- `gamification/` - Points, badges, leaderboards, and achievements
- `analytics/` - Learning analytics and AI-driven insights
- `api/` - Django REST framework API endpoints
- `templates/`: HTML templates for rendering pages
  - `courses/`: Templates for course-related pages
  - `courses/content_types/`: Templates for different content types (video, blog, quiz)
  - `courses/instructor/`: Templates for instructor-facing pages
- `static/`: Static files (CSS, JavaScript, images)
- `media/`: User-uploaded files

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Django - The web framework used
- Bootstrap - For responsive design
- FullCalendar - For the study planner calendar
- Chart.js - For data visualization