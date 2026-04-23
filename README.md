Django REST API backend for WHALMMS learning management system.

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
copy .env.example .env
```

4. Configure your `.env` file with SMTP credentials (see Password Reset section below).

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run development server:
```bash
python manage.py runserver
```

Add these variables to your `.env` file:

```env
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER='your-email@gmail.com'
EMAIL_HOST_PASSWORD='your-app-password'
DEFAULT_FROM_EMAIL='your-email@gmail.com'
```

**For Gmail:**
1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Generate an App Password: https://myaccount.google.com/apppasswords
4. Use that app password in `EMAIL_HOST_PASSWORD`

```http
POST /api/auth/password/reset/
Content-Type: application/json

{
  "email": "user@example.com",
  "frontend_url": "http://localhost:5173"  // optional, defaults to http://localhost:5173
}
```

**Response:**
```json
{
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

This sends an email to the user with a password reset link containing a unique, time-limited token.

```http
POST /api/auth/password/reset/confirm/
Content-Type: application/json

{
  "uid": "encoded_uid_from_email_link",
  "token": "token_from_email_link",
  "new_password": "newSecurePassword123"
}
```

**Response:**
```json
{
  "message": "Password has been reset successfully"
}
```

1. User requests password reset via `/api/auth/password/reset/`
2. Backend generates secure token (1-hour expiration)
3. Email sent to user with reset link: `{frontend_url}/reset-password/{uid}/{token}/`
4. User clicks link → frontend extracts uid/token from URL
5. User enters new password → frontend calls `/api/auth/password/reset/confirm/`
6. Backend validates token and updates password

- Tokens expire after 1 hour
- Tokens are single-use
- Email enumeration protection (same response whether email exists or not)
- Cryptographically secure token generation via Django's `default_token_generator`

Optional: Populate database with sample data:
```bash
python seed_data.py
```

- `POST /api/register/` - Register new user
- `POST /api/token/` - Login (JWT)
- `POST /api/token/refresh/` - Refresh JWT token
- `GET /api/users/me/` - Get current user
- `POST /api/auth/password/reset/` - Request password reset
- `POST /api/auth/password/reset/confirm/` - Confirm password reset

- `GET /api/admin/users/` - List users (admin only)
- `GET /api/admin/users/<id>/` - Get user detail (admin only)
- `PATCH /api/admin/users/<id>/` - Update user (admin only)
- `DELETE /api/admin/users/<id>/` - Delete user (admin only)

- `GET /api/courses/` - List all courses
- `POST /api/courses/` - Create course
- `GET /api/courses/<id>/` - Get course detail
- `PUT/PATCH /api/courses/<id>/` - Update course
- `DELETE /api/courses/<id>/` - Delete course
- `POST /api/courses/<id>/enroll/` - Enroll in course

- `GET /api/quizzes/` - List all quizzes
- `POST /api/quizzes/` - Create quiz
- `GET /api/quizzes/<id>/` - Get quiz detail
- `POST /api/quizzes/<id>/submit/` - Submit quiz answers
- `GET /api/quizzes/<id>/attempts/` - Get quiz attempts
