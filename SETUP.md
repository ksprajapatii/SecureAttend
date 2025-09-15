# SecureAttend Setup Guide

This guide provides step-by-step instructions for setting up SecureAttend on your local machine.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 18.04+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Python**: 3.11 or higher
- **MySQL**: 8.0 or higher
- **Redis**: 6.0 or higher

### Recommended Requirements
- **RAM**: 16GB
- **Storage**: 10GB free space
- **CPU**: Multi-core processor
- **Webcam**: For face recognition testing

## 🛠️ Installation Steps

### Step 1: Install System Dependencies

#### Windows
```bash
# Install Python 3.11+
# Download from: https://www.python.org/downloads/

# Install MySQL 8.0
# Download from: https://dev.mysql.com/downloads/mysql/

# Install Redis
# Download from: https://github.com/microsoftarchive/redis/releases

# Install Git
# Download from: https://git-scm.com/downloads
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 mysql redis git
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install python3.11 python3.11-venv python3.11-dev
sudo apt install mysql-server redis-server git
sudo apt install build-essential cmake pkg-config
sudo apt install libopencv-dev libgtk-3-dev libboost-python-dev
```

### Step 2: Clone the Repository
```bash
git clone <repository-url>
cd SecureAttend
```

### Step 3: Create Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 4: Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 5: Database Setup

#### Start MySQL Service
```bash
# Windows: Start MySQL service from Services
# macOS:
brew services start mysql
# Ubuntu/Debian:
sudo systemctl start mysql
```

#### Create Database
```bash
# Connect to MySQL
mysql -u root -p

# Create database
CREATE DATABASE secureattend_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user (optional)
CREATE USER 'secureattend_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON secureattend_db.* TO 'secureattend_user'@'localhost';
FLUSH PRIVILEGES;

# Exit MySQL
exit;
```

### Step 6: Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

#### Update .env file with your settings:
```env
# Database settings
DB_NAME=secureattend_db
DB_USER=root  # or secureattend_user
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# Email settings (optional for testing)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Other settings can remain default for local development
```

### Step 7: Database Migration
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Step 8: Download Face Recognition Models
```bash
# Create necessary directories
mkdir -p logs media face_encodings

# The system will automatically download the face landmark model on first run
# Or download manually:
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
```

### Step 9: Start Services

#### Terminal 1: Start Redis
```bash
# Windows: Start Redis server from Start Menu
# macOS:
brew services start redis
# Ubuntu/Debian:
sudo systemctl start redis
# Or run directly:
redis-server
```

#### Terminal 2: Start Celery Worker
```bash
# Activate virtual environment first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Celery worker
celery -A secureattend worker --loglevel=info
```

#### Terminal 3: Start Celery Beat (Optional)
```bash
# Start Celery beat for scheduled tasks
celery -A secureattend beat --loglevel=info
```

#### Terminal 4: Start Django Server
```bash
# Activate virtual environment first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Django development server
python manage.py runserver
```

### Step 10: Verify Installation
1. Open browser and go to: http://localhost:8000
2. You should see the SecureAttend login page
3. Login with your superuser credentials
4. Navigate to the dashboard to verify everything is working

## 🧪 Testing the Installation

### Test Face Recognition
1. Go to the Users section in the dashboard
2. Add a new user with a clear face photo
3. The system should automatically generate face encodings
4. Test recognition using the API or web interface

### Test Liveness Detection
1. Use the face recognition API with a live photo
2. Check that liveness detection returns appropriate scores
3. Test with a static photo to verify anti-spoofing works

### Test Email Notifications
1. Configure email settings in .env
2. Trigger an anomaly alert
3. Check that email notifications are sent

## 🔧 Configuration Options

### Face Recognition Settings
Edit `secureattend/settings.py`:
```python
# Face recognition model (hog = faster, cnn = more accurate)
FACE_RECOGNITION_MODEL = 'hog'

# Recognition confidence threshold
FACE_RECOGNITION_THRESHOLD = 0.6

# Liveness detection threshold
LIVENESS_THRESHOLD = 0.3

# Blink detection threshold
BLINK_THRESHOLD = 0.25

# Head pose threshold (degrees)
HEAD_POSE_THRESHOLD = 30
```

### Email Configuration
Update `.env` file:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=SecureAttend <noreply@secureattend.com>
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. MySQL Connection Error
```bash
# Check MySQL service status
# Windows: Check Services
# macOS: brew services list | grep mysql
# Ubuntu: sudo systemctl status mysql

# Test connection
mysql -u root -p -e "SELECT 1;"
```

#### 2. Redis Connection Error
```bash
# Check Redis service status
# Windows: Check if Redis is running
# macOS: brew services list | grep redis
# Ubuntu: sudo systemctl status redis

# Test connection
redis-cli ping
```

#### 3. Face Recognition Not Working
```bash
# Check if OpenCV is properly installed
python -c "import cv2; print(cv2.__version__)"

# Check if face_recognition is installed
python -c "import face_recognition; print('OK')"

# Check if dlib is installed
python -c "import dlib; print('OK')"
```

#### 4. Permission Errors
```bash
# Fix file permissions
chmod +x manage.py
chmod -R 755 media/
chmod -R 755 logs/
```

#### 5. Port Already in Use
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
# macOS/Linux:
lsof -i :8000

# Kill process or use different port
python manage.py runserver 8001
```

### Log Files
Check these log files for errors:
- `logs/secureattend.log` - Django application logs
- `logs/gunicorn_error.log` - Gunicorn error logs (if using)
- `logs/gunicorn_access.log` - Gunicorn access logs (if using)

### Debug Mode
Enable debug mode in `.env`:
```env
DEBUG=True
```

This will show detailed error messages in the browser.

## 📚 Next Steps

After successful installation:

1. **Add Users**: Create user profiles with face photos
2. **Test Recognition**: Verify face recognition works correctly
3. **Configure Alerts**: Set up email notifications
4. **Customize Settings**: Adjust thresholds and parameters
5. **API Integration**: Test API endpoints
6. **Production Setup**: Configure for production deployment

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review the log files for error messages
3. Ensure all dependencies are properly installed
4. Verify database and Redis connections
5. Check the GitHub issues page for similar problems

## 🔄 Updates

To update SecureAttend:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Restart services
```

---

**Note**: This setup guide is for local development. For production deployment, see the main README.md file for Docker and production configuration options.
