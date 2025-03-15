# EduMate - Learn, Play, Achieve!

EduMate is a gamified EdTech web application designed to enhance learning engagement and retention through AI-driven personalization and game mechanics. The platform addresses the challenges of passive learning by integrating elements such as points, badges, leaderboards, and adaptive learning insights, ensuring a highly interactive and motivating educational experience.

## Features

- **AI-Powered Personalization:** Adapts content difficulty based on learner performance and engagement.
- **Dynamic Challenges & Rewards:** Provides interactive challenges and rewards for progress.
- **Leaderboard & Social Engagement:** Encourages competition and collaboration among learners.
- **Real-Time Feedback:** Offers instant AI-generated insights to guide learners effectively.
- **Gamified Learning Modules:** Incorporates quizzes, missions, and streak tracking to sustain motivation.
- **Learning Analytics Dashboard:** Enables tracking of user progress, strengths, and improvement areas.

## Technology Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, Bootstrap, JavaScript
- **Database:** PostgreSQL (SQLite for development)
- **AI/ML Integration:** Deepseek, ChatGPT

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/edumate.git
   cd edumate
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

8. Access the application at http://127.0.0.1:8000/

## Project Structure

- `accounts/` - User authentication and profile management
- `courses/` - Course content and learning modules
- `gamification/` - Points, badges, leaderboards, and achievements
- `analytics/` - Learning analytics and AI-driven insights
- `api/` - Django REST framework API endpoints

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For any questions or feedback, please contact [your-email@example.com](mailto:your-email@example.com). 