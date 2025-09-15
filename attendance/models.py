"""
Models for the attendance system.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid


class UserProfile(models.Model):
    """Extended user profile with face recognition data."""
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    photo = models.ImageField(
        upload_to='user_photos/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text="Upload a clear photo of your face for recognition"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    face_encoding = models.TextField(blank=True, null=True, help_text="Stored face encoding for recognition")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.name} ({self.role})"


class AttendanceRecord(models.Model):
    """Attendance records with liveness and mask detection."""
    
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Unknown', 'Unknown'),
    ]
    
    MASK_STATUS_CHOICES = [
        ('With Mask', 'With Mask'),
        ('Without Mask', 'Without Mask'),
    ]
    
    LIVENESS_STATUS_CHOICES = [
        ('Live', 'Live'),
        ('Spoof', 'Spoof'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    mask_status = models.CharField(max_length=20, choices=MASK_STATUS_CHOICES, default='Without Mask')
    liveness_status = models.CharField(max_length=20, choices=LIVENESS_STATUS_CHOICES, default='Live')
    anomaly_flag = models.BooleanField(default=False, help_text="Flag for spoofing attempts or anomalies")
    confidence_score = models.FloatField(default=0.0, help_text="Recognition confidence score")
    liveness_score = models.FloatField(default=0.0, help_text="Liveness detection score")
    captured_image = models.ImageField(
        upload_to='attendance_images/',
        blank=True,
        null=True,
        help_text="Image captured during attendance"
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or comments")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-time']
        unique_together = ['user', 'date']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.user.name} - {self.date} ({self.status})"


class AnomalyAlert(models.Model):
    """Alerts for suspicious activities and spoofing attempts."""
    
    ALERT_TYPE_CHOICES = [
        ('spoof_attempt', 'Spoofing Attempt'),
        ('multiple_faces', 'Multiple Faces Detected'),
        ('no_face', 'No Face Detected'),
        ('low_confidence', 'Low Recognition Confidence'),
        ('mask_violation', 'Mask Policy Violation'),
        ('unknown_person', 'Unknown Person Detected'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    attendance_record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    details = models.JSONField(default=dict, help_text="Additional alert details")
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Anomaly Alert'
        verbose_name_plural = 'Anomaly Alerts'
    
    def __str__(self):
        return f"{self.alert_type} - {self.severity} ({self.created_at})"


class SystemSettings(models.Model):
    """System configuration settings."""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return f"{self.key}: {self.value}"
