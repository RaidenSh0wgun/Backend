"""
Single-file seeder for dummy data.
Run with: python manage.py shell < seed_data.py
"""
import os
import sys
import random
from datetime import date, timedelta, datetime
from django.utils import timezone
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User
from user.models import StudentProfile, InstructorProfile
from course.models import Course, Enrollment
from quiz.models import Quiz, Question, Answer, QuizAttempt

# ── Configuration ──────────────────────────────────────────────────────────
NUM_COURSES = 30
NUM_TEACHERS = 15
NUM_STUDENTS = 50
MIN_QUIZZES_PER_COURSE = 30
MAX_QUIZZES_PER_COURSE = 50
MIN_QUESTIONS_PER_QUIZ = 3
MAX_QUESTIONS_PER_QUIZ = 10
PASSKEY = "123"
USER_PASSWORD = "Password123"
QUESTION_TYPES = [
    Question.TYPE_IDENTIFICATION,
    Question.TYPE_ENUMERATION,
    Question.TYPE_MULTIPLE_CHOICE,
    Question.TYPE_TRUE_FALSE,
]

# ── Helper ─────────────────────────────────────────────────────────────────
def get_or_create_user(username, email, first_name, last_name, is_staff=False):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": is_staff,
        },
    )
    if created:
        user.set_password(USER_PASSWORD)
        user.save()
    return user, created


# ── Step 0: Clear existing data (in reverse dependency order) ──────────────
print("🗑  Clearing existing data...")
Answer.objects.all().delete()
Question.objects.all().delete()
QuizAttempt.objects.all().delete()
Quiz.objects.all().delete()
Enrollment.objects.all().delete()
Course.objects.all().delete()
StudentProfile.objects.all().delete()
InstructorProfile.objects.all().delete()
User.objects.all().delete()
print("✅ Database cleared.")

# ── Step 1: Create 15 teachers ─────────────────────────────────────────────
print(f"👨‍🏫 Creating {NUM_TEACHERS} teachers...")
teachers = []
for i in range(1, NUM_TEACHERS + 1):
    username = f"teacher{i}"
    user, _ = get_or_create_user(
        username=username,
        email=f"{username}@example.com",
        first_name=f"Teacher",
        last_name=f"{i}",
    )
    profile, _ = InstructorProfile.objects.get_or_create(
        user=user,
        defaults={
            "department": random.choice(["Math", "Science", "English", "History", "CS", "Arts"]),
            "full_name": f"Teacher {i}",
        },
    )
    teachers.append(profile)
print(f"✅ Created {len(teachers)} teachers.")

# ── Step 2: Create 30 courses ──────────────────────────────────────────────
print(f"📚 Creating {NUM_COURSES} courses...")
course_titles = [
    "Introduction to Calculus",
    "Linear Algebra Fundamentals",
    "Organic Chemistry I",
    "General Biology",
    "Physics Mechanics",
    "English Composition",
    "Creative Writing",
    "World History",
    "American Government",
    "Introduction to Psychology",
    "Sociology Basics",
    "Macroeconomics",
    "Microeconomics",
    "Data Structures & Algorithms",
    "Web Development 101",
    "Database Management",
    "Computer Networks",
    "Operating Systems",
    "Discrete Mathematics",
    "Statistics for Data Science",
    "Machine Learning Basics",
    "Digital Logic Design",
    "Software Engineering",
    "Artificial Intelligence",
    "Cybersecurity Fundamentals",
    "Mobile App Development",
    "Cloud Computing",
    "Game Development",
    "UI/UX Design Principles",
    "Blockchain Technology",
]

courses = []
for i in range(NUM_COURSES):
    teacher = teachers[i % NUM_TEACHERS]  # distributes evenly, some teachers get 2
    has_passkey = random.choice([True, False])
    course = Course.objects.create(
        title=course_titles[i],
        description=f"This is the course description for {course_titles[i]}.",
        is_active=True,
        author=teacher,
        passkey=PASSKEY if has_passkey else None,
    )
    teacher.assigned_courses.add(course)
    courses.append(course)
print(f"✅ Created {len(courses)} courses.")

# ── Step 3: Create 50 students ─────────────────────────────────────────────
print(f"👨‍🎓 Creating {NUM_STUDENTS} students...")
students = []
for i in range(1, NUM_STUDENTS + 1):
    username = f"student{i}"
    user, _ = get_or_create_user(
        username=username,
        email=f"{username}@example.com",
        first_name=f"Student",
        last_name=f"{i}",
    )
    profile, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            "full_name": f"Student {i}",
        },
    )
    students.append(profile)
print(f"✅ Created {len(students)} students.")

# ── Step 4: Enroll students in random courses ──────────────────────────────
print("📝 Enrolling students in random courses...")
for student in students:
    num_courses = random.randint(1, 6)
    enrolled_courses = random.sample(courses, num_courses)
    for course in enrolled_courses:
        Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={
                "used_passkey": PASSKEY if course.passkey else "",
            },
        )
        student.enrolled_courses.add(course)
print("✅ Enrollment complete.")

# ── Step 5: Create quizzes, questions, and answers ─────────────────────────
print("📝 Creating quizzes, questions, and answers...")
quiz_counter = 0

# Date range for due dates: today (April 10, 2026) to July 31, 2026
start_date = date(2026, 4, 10)
end_date = date(2026, 7, 31)
date_range_days = (end_date - start_date).days

for course in courses:
    num_quizzes = random.randint(MIN_QUIZZES_PER_COURSE, MAX_QUIZZES_PER_COURSE)
    for j in range(1, num_quizzes + 1):
        quiz_counter += 1
        # Generate random due date within the range
        random_days = random.randint(0, date_range_days)
        due_date = start_date + timedelta(days=random_days)
        
        quiz_title = f"{course.title} - Quiz {j} (#{quiz_counter})"
        # Create timezone-aware datetime at midnight UTC
        due_date_dt = timezone.make_aware(datetime.combine(due_date, datetime.min.time()))
        quiz = Quiz.objects.create(
            author=course.author,
            course=course,
            title=quiz_title,
            description=f"Quiz for {course.title}, number {j}.",
            duration_minutes=random.randint(10, 60),
            is_active=True,
            due_date=due_date_dt,
        )

        num_questions = random.randint(MIN_QUESTIONS_PER_QUIZ, MAX_QUESTIONS_PER_QUIZ)
        for k in range(num_questions):
            q_type = QUESTION_TYPES[k % len(QUESTION_TYPES)]
            question = Question.objects.create(
                quiz=quiz,
                text="question?",
                question_type=q_type,
                correct_text="right",
            )

            if q_type == Question.TYPE_TRUE_FALSE:
                Answer.objects.create(Question=question, answer_text="right", is_correct=True)
                Answer.objects.create(Question=question, answer_text="wrong", is_correct=False)
            elif q_type == Question.TYPE_MULTIPLE_CHOICE:
                Answer.objects.create(Question=question, answer_text="right", is_correct=True)
                Answer.objects.create(Question=question, answer_text="wrong", is_correct=False)
                Answer.objects.create(Question=question, answer_text="wrong", is_correct=False)
                Answer.objects.create(Question=question, answer_text="wrong", is_correct=False)
            else:
                # identification / enumeration — just the correct answer
                Answer.objects.create(Question=question, answer_text="right", is_correct=True)

print(f"✅ Created {quiz_counter} quizzes with questions and answers.")

# ── Done ───────────────────────────────────────────────────────────────────
print("\n🎉 SEEDING COMPLETE!")
print(f"   Teachers:   {NUM_TEACHERS}")
print(f"   Students:   {NUM_STUDENTS}")
print(f"   Courses:    {NUM_COURSES}")
print(f"   Quizzes:    {quiz_counter}")
print(f"   Password:   {USER_PASSWORD}")
print(f"   Passkey:    {PASSKEY}")
print(f"\n   Superuser:  NOT created — run `python manage.py createsuperuser` if you need admin access.")
