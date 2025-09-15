<<<<<<< HEAD
# SecureAttend - Liveness-Enabled Face Recognition Attendance System

A comprehensive, industry-ready face recognition attendance system built with Django, featuring liveness detection, mask detection, and real-time anomaly alerts.

## 🎯 Features

### Core Features
- **Face Recognition** - Real-time face detection and recognition using OpenCV and face_recognition
- **Liveness Detection** - Anti-spoofing protection using blink detection and head pose estimation
- **Mask Detection** - Automatic detection of face masks for compliance monitoring
- **Attendance Database** - Comprehensive logging with date, time, user, mask, and liveness status
- **Admin Dashboard** - Modern Bootstrap-based web interface for management
- **Anomaly Alerts** - Real-time email notifications for spoofing attempts and security issues

### Advanced Features
- **REST API** - Complete API for external system integration
- **JWT Authentication** - Secure token-based authentication
- **Async Processing** - Celery-based background tasks for email alerts
- **Export Functionality** - CSV/PDF export of attendance reports
- **Multi-role Support** - Student, Faculty, and Admin roles
- **Compliance Monitoring** - Mask and liveness compliance tracking

## 🏗️ Tech Stack

- **Backend**: Django 5.x + Django REST Framework
- **Database**: MySQL 8.0
- **Frontend**: Django Templates + Bootstrap 5
- **Face Recognition**: OpenCV + face_recognition + dlib
- **Liveness Detection**: Custom implementation with eye aspect ratio and head pose
- **Async Tasks**: Celery + Redis
- **Authentication**: JWT (JSON Web Tokens)
- **Deployment**: Docker + Nginx + Gunicorn

## 📋 Prerequisites

- Python 3.11+
- MySQL 8.0+
- Redis 6.0+
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd SecureAttend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE secureattend_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit
```

### 5. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
nano .env
```

### 6. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Download Face Landmark Model
```bash
# The system will automatically download the required model on first run
# Or manually download:
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
```

### 9. Start Services
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A secureattend worker --loglevel=info

# Terminal 3: Start Celery Beat (for scheduled tasks)
celery -A secureattend beat --loglevel=info

# Terminal 4: Start Django Server
python manage.py runserver
```

### 10. Access the Application
- **Web Dashboard**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build
```bash
# Build image
docker build -t secureattend .

# Run with docker-compose or manually with linked containers
```

## 📊 Usage Guide

### 1. User Management
1. Access the admin dashboard at http://localhost:8000
2. Login with your superuser credentials
3. Navigate to "Users" to add new users
4. Upload clear face photos for each user
5. The system will automatically generate face encodings

### 2. Face Recognition API
```python
import requests

# Recognize face from image
with open('user_photo.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:8000/api/recognize-face/', files=files)
    result = response.json()
    print(f"Recognized: {result['user_name']} (Confidence: {result['confidence']})")
```

### 3. Mark Attendance
```python
# Mark attendance for recognized user
attendance_data = {
    'user_id': 'user-uuid',
    'confidence': 0.95,
    'liveness_score': 0.88,
    'is_live': True,
    'has_mask': False
}
response = requests.post('http://localhost:8000/api/mark-attendance/', json=attendance_data)
```

### 4. View Reports
- Access the dashboard for real-time statistics
- Export attendance data in CSV/PDF format
- Monitor anomaly alerts and security events

## 🔧 Configuration

### Face Recognition Settings
```python
# In settings.py
FACE_RECOGNITION_MODEL = 'hog'  # or 'cnn' for better accuracy
FACE_RECOGNITION_THRESHOLD = 0.6  # Recognition confidence threshold
LIVENESS_THRESHOLD = 0.3  # Liveness detection threshold
BLINK_THRESHOLD = 0.25  # Eye aspect ratio threshold
HEAD_POSE_THRESHOLD = 30  # Head pose angle threshold
```

### Email Configuration
```python
# Configure SMTP settings in .env
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## 🔒 Security Features

### Authentication
- JWT-based API authentication
- Role-based access control (Student, Faculty, Admin)
- Session-based web authentication

### Anti-Spoofing
- Blink detection using eye aspect ratio
- Head pose estimation for movement detection
- Confidence scoring for recognition accuracy
- Anomaly flagging for suspicious activities

### Data Protection
- Encrypted face encodings storage
- Secure file upload handling
- IP address and user agent logging
- Comprehensive audit trails

## 📈 Monitoring and Alerts

### Real-time Monitoring
- Live attendance statistics
- Compliance rate tracking
- Anomaly detection alerts
- System health monitoring

### Email Notifications
- Immediate alerts for spoofing attempts
- Daily attendance reports
- System maintenance notifications
- Security incident reports

## 🛠️ API Reference

### Authentication
```bash
# Get JWT token
POST /api/auth/token/
{
    "username": "your_username",
    "password": "your_password"
}

# Refresh token
POST /api/auth/token/refresh/
{
    "refresh": "your_refresh_token"
}
```

### Face Recognition
```bash
# Recognize face
POST /api/recognize-face/
Content-Type: multipart/form-data
{
    "image": <image_file>,
    "check_liveness": true,
    "check_mask": true
}
```

### Attendance Management
```bash
# Mark attendance
POST /api/mark-attendance/
{
    "user_id": "uuid",
    "confidence": 0.95,
    "liveness_score": 0.88,
    "is_live": true,
    "has_mask": false
}

# Get attendance records
GET /api/attendance/?user_id=uuid&date_from=2024-01-01&date_to=2024-01-31
```

### User Management
```bash
# List users
GET /api/users/

# Create user
POST /api/users/
{
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student",
    "username": "johndoe",
    "password": "secure_password",
    "photo": <image_file>
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Face Recognition Not Working**
   - Ensure face photos are clear and well-lit
   - Check if face encodings are generated
   - Verify OpenCV and dlib installation

2. **Liveness Detection Issues**
   - Ensure good lighting conditions
   - Check if dlib landmark predictor is downloaded
   - Verify camera permissions

3. **Database Connection Errors**
   - Check MySQL service status
   - Verify database credentials in .env
   - Ensure database exists and is accessible

4. **Celery Tasks Not Running**
   - Check Redis service status
   - Verify Celery worker is running
   - Check task queue in Redis

### Logs and Debugging
```bash
# View Django logs
tail -f logs/secureattend.log

# View Celery logs
celery -A secureattend worker --loglevel=debug

# Check Redis
redis-cli ping
```

## 📝 Development

### Project Structure
```
SecureAttend/
├── attendance/           # Main attendance app
├── face_recognition_app/ # Face recognition module
├── secureattend/        # Django project settings
├── templates/           # HTML templates
├── static/             # Static files
├── media/              # User uploads
├── logs/               # Application logs
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker configuration
└── README.md          # This file
```

### Adding New Features
1. Create new Django app: `python manage.py startapp new_feature`
2. Add to INSTALLED_APPS in settings.py
3. Create models, views, and URLs
4. Add tests and documentation
5. Update API documentation

### Testing
```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🚀 Production Deployment

### Environment Setup
1. Set `DEBUG=False` in production
2. Use strong secret keys
3. Configure proper database credentials
4. Set up SSL certificates
5. Configure email settings
6. Set up monitoring and logging

### Performance Optimization
- Use Redis for caching
- Configure database connection pooling
- Enable Gunicorn worker processes
- Use CDN for static files
- Implement database indexing

### Security Hardening
- Enable HTTPS
- Configure security headers
- Use strong passwords
- Regular security updates
- Monitor access logs

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks
- Update dependencies regularly
- Monitor system logs
- Clean up old attendance records
- Backup database regularly
- Update face encodings as needed

### Version Updates
- Follow semantic versioning
- Update documentation
- Test thoroughly before deployment
- Maintain backward compatibility

---

**SecureAttend** - Secure, Reliable, and Intelligent Face Recognition Attendance System
=======
# SecureAttend
This is face recognising system 
>>>>>>> 6fa33ed7ace3867f46ff30c068121264e3395640
