# SecureAttend API Documentation

This document provides comprehensive API documentation for the SecureAttend face recognition attendance system.

## 🔐 Authentication

SecureAttend uses JWT (JSON Web Tokens) for API authentication.

### Get Access Token
```http
POST /api/auth/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Refresh Access Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "your_refresh_token"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using Tokens
Include the access token in the Authorization header:
```http
Authorization: Bearer your_access_token
```

## 👥 User Management

### List Users
```http
GET /api/users/
Authorization: Bearer your_access_token
```

**Response:**
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "user": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": true
            },
            "name": "John Doe",
            "email": "john@example.com",
            "photo": "/media/user_photos/john_photo.jpg",
            "photo_url": "http://localhost:8000/media/user_photos/john_photo.jpg",
            "role": "student",
            "is_active": true,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### Get User Details
```http
GET /api/users/{user_id}/
Authorization: Bearer your_access_token
```

### Create User
```http
POST /api/users/
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "username": "janesmith",
    "password": "secure_password123",
    "role": "faculty",
    "photo": <image_file>
}
```

### Update User
```http
PATCH /api/users/{user_id}/
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

{
    "name": "Jane Smith Updated",
    "role": "admin",
    "is_active": true,
    "photo": <new_image_file>
}
```

### Delete User
```http
DELETE /api/users/{user_id}/
Authorization: Bearer your_access_token
```

## 📅 Attendance Management

### List Attendance Records
```http
GET /api/attendance/
Authorization: Bearer your_access_token
```

**Query Parameters:**
- `user_id`: Filter by user ID
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `page`: Page number for pagination

**Example:**
```http
GET /api/attendance/?user_id=123e4567-e89b-12d3-a456-426614174000&date_from=2024-01-01&date_to=2024-01-31
```

**Response:**
```json
{
    "count": 50,
    "next": "http://localhost:8000/api/attendance/?page=2",
    "previous": null,
    "results": [
        {
            "id": "456e7890-e89b-12d3-a456-426614174001",
            "user": "123e4567-e89b-12d3-a456-426614174000",
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "date": "2024-01-15",
            "time": "09:30:00",
            "status": "Present",
            "mask_status": "With Mask",
            "liveness_status": "Live",
            "anomaly_flag": false,
            "confidence_score": 0.95,
            "liveness_score": 0.88,
            "captured_image": "/media/attendance_images/attendance_456e7890.jpg",
            "captured_image_url": "http://localhost:8000/media/attendance_images/attendance_456e7890.jpg",
            "ip_address": "192.168.1.100",
            "notes": null,
            "created_at": "2024-01-15T09:30:00Z"
        }
    ]
}
```

### Get Attendance Record
```http
GET /api/attendance/{record_id}/
Authorization: Bearer your_access_token
```

### Create Attendance Record
```http
POST /api/attendance/
Authorization: Bearer your_access_token
Content-Type: application/json

{
    "user": "123e4567-e89b-12d3-a456-426614174000",
    "date": "2024-01-15",
    "time": "09:30:00",
    "status": "Present",
    "mask_status": "With Mask",
    "liveness_status": "Live",
    "confidence_score": 0.95,
    "liveness_score": 0.88,
    "captured_image": <base64_encoded_image>,
    "ip_address": "192.168.1.100",
    "notes": "Regular attendance"
}
```

## 🎭 Face Recognition

### Recognize Face
```http
POST /api/recognize-face/
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

{
    "image": <image_file>,
    "check_liveness": true,
    "check_mask": true
}
```

**Response:**
```json
{
    "recognized": true,
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_name": "John Doe",
    "confidence": 0.95,
    "liveness_score": 0.88,
    "is_live": true,
    "has_mask": false,
    "face_locations": [[100, 200, 300, 150]],
    "anomaly_detected": false
}
```

### Mark Attendance
```http
POST /api/mark-attendance/
Authorization: Bearer your_access_token
Content-Type: application/json

{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "confidence": 0.95,
    "liveness_score": 0.88,
    "is_live": true,
    "has_mask": false,
    "captured_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

**Response:**
```json
{
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "user": "123e4567-e89b-12d3-a456-426614174000",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "date": "2024-01-15",
    "time": "09:30:00",
    "status": "Present",
    "mask_status": "Without Mask",
    "liveness_status": "Live",
    "anomaly_flag": false,
    "confidence_score": 0.95,
    "liveness_score": 0.88,
    "captured_image": "/media/attendance_images/attendance_456e7890.jpg",
    "captured_image_url": "http://localhost:8000/media/attendance_images/attendance_456e7890.jpg",
    "ip_address": "192.168.1.100",
    "notes": null,
    "created_at": "2024-01-15T09:30:00Z"
}
```

## 🚨 Anomaly Alerts

### List Alerts
```http
GET /api/alerts/
Authorization: Bearer your_access_token
```

**Query Parameters:**
- `is_resolved`: Filter by resolution status (true/false)
- `alert_type`: Filter by alert type
- `severity`: Filter by severity level

**Response:**
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "789e0123-e89b-12d3-a456-426614174002",
            "alert_type": "spoof_attempt",
            "severity": "high",
            "user": "123e4567-e89b-12d3-a456-426614174000",
            "user_name": "John Doe",
            "attendance_record": "456e7890-e89b-12d3-a456-426614174001",
            "message": "Spoofing attempt detected during face recognition",
            "details": {
                "confidence": 0.45,
                "liveness_score": 0.12,
                "has_mask": false,
                "face_location": [100, 200, 300, 150]
            },
            "is_resolved": false,
            "resolved_by": null,
            "resolved_by_name": null,
            "resolved_at": null,
            "created_at": "2024-01-15T09:30:00Z"
        }
    ]
}
```

### Get Alert Details
```http
GET /api/alerts/{alert_id}/
Authorization: Bearer your_access_token
```

### Resolve Alert
```http
PATCH /api/alerts/{alert_id}/
Authorization: Bearer your_access_token
Content-Type: application/json

{
    "is_resolved": true
}
```

## 📊 Statistics

### Get Attendance Statistics
```http
GET /api/stats/
Authorization: Bearer your_access_token
```

**Response:**
```json
{
    "total_users": 150,
    "present_today": 120,
    "absent_today": 30,
    "total_attendance_records": 1500,
    "anomaly_alerts_today": 3,
    "mask_compliance_rate": 85.5,
    "liveness_success_rate": 92.3
}
```

## 🔧 Face Recognition App APIs

### Test Face Recognition
```http
POST /api/face/recognize/
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

{
    "image": <image_file>
}
```

### Add Face Encoding
```http
POST /api/face/add-face/
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "image": <image_file>
}
```

### Test Liveness Detection
```http
POST /api/face/test-liveness/
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

{
    "image": <image_file>
}
```

## 📝 Error Responses

### Authentication Error
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Validation Error
```json
{
    "field_name": [
        "This field is required."
    ]
}
```

### Not Found Error
```json
{
    "detail": "Not found."
}
```

### Server Error
```json
{
    "error": "Internal server error"
}
```

## 🔍 Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## 📋 Rate Limiting

API requests are rate-limited to prevent abuse:
- **Authentication endpoints**: 5 requests per minute
- **Face recognition**: 10 requests per minute
- **Other endpoints**: 100 requests per minute

## 🔒 Security Considerations

1. **Always use HTTPS** in production
2. **Store tokens securely** and refresh them regularly
3. **Validate all input data** before processing
4. **Implement proper error handling** in your client
5. **Monitor API usage** for suspicious activity

## 📚 Example Usage

### Python Example
```python
import requests
import base64

# Authentication
auth_response = requests.post('http://localhost:8000/api/auth/token/', {
    'username': 'your_username',
    'password': 'your_password'
})
token = auth_response.json()['access']

headers = {'Authorization': f'Bearer {token}'}

# Face Recognition
with open('user_photo.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post(
        'http://localhost:8000/api/recognize-face/',
        files=files,
        headers=headers
    )
    result = response.json()
    print(f"Recognized: {result['user_name']}")

# Mark Attendance
attendance_data = {
    'user_id': result['user_id'],
    'confidence': result['confidence'],
    'liveness_score': result['liveness_score'],
    'is_live': result['is_live'],
    'has_mask': result['has_mask']
}
response = requests.post(
    'http://localhost:8000/api/mark-attendance/',
    json=attendance_data,
    headers=headers
)
```

### JavaScript Example
```javascript
// Authentication
const authResponse = await fetch('http://localhost:8000/api/auth/token/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: 'your_username',
        password: 'your_password'
    })
});
const { access } = await authResponse.json();

// Face Recognition
const formData = new FormData();
formData.append('image', imageFile);

const response = await fetch('http://localhost:8000/api/recognize-face/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access}`
    },
    body: formData
});
const result = await response.json();
console.log(`Recognized: ${result.user_name}`);
```

---

For more information, see the main README.md file or contact the development team.
