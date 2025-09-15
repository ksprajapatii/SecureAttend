"""
Serializers for the attendance API.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, AttendanceRecord, AnomalyAlert, SystemSettings


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    user = UserSerializer(read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'name', 'email', 'photo', 'photo_url', 
            'role', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_photo_url(self, obj):
        """Get the URL of the user's photo."""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
        return None


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating UserProfile."""
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    
    class Meta:
        model = UserProfile
        fields = [
            'name', 'email', 'photo', 'role', 'username', 'password'
        ]
    
    def create(self, validated_data):
        """Create a new user and profile."""
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        # Create Django User
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=password
        )
        
        # Create UserProfile
        profile = UserProfile.objects.create(
            user=user,
            **validated_data
        )
        
        return profile


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceRecord model."""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    captured_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'user', 'user_name', 'user_email', 'date', 'time', 
            'status', 'mask_status', 'liveness_status', 'anomaly_flag',
            'confidence_score', 'liveness_score', 'captured_image', 
            'captured_image_url', 'ip_address', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_captured_image_url(self, obj):
        """Get the URL of the captured image."""
        if obj.captured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.captured_image.url)
        return None


class AttendanceRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AttendanceRecord."""
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'user', 'date', 'time', 'status', 'mask_status', 
            'liveness_status', 'confidence_score', 'liveness_score',
            'captured_image', 'ip_address', 'notes'
        ]


class AnomalyAlertSerializer(serializers.ModelSerializer):
    """Serializer for AnomalyAlert model."""
    user_name = serializers.CharField(source='user.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = AnomalyAlert
        fields = [
            'id', 'alert_type', 'severity', 'user', 'user_name',
            'attendance_record', 'message', 'details', 'is_resolved',
            'resolved_by', 'resolved_by_name', 'resolved_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SystemSettings model."""
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FaceRecognitionRequestSerializer(serializers.Serializer):
    """Serializer for face recognition requests."""
    image = serializers.ImageField()
    check_liveness = serializers.BooleanField(default=True)
    check_mask = serializers.BooleanField(default=True)


class FaceRecognitionResponseSerializer(serializers.Serializer):
    """Serializer for face recognition responses."""
    recognized = serializers.BooleanField()
    user_id = serializers.CharField(allow_null=True)
    user_name = serializers.CharField(allow_null=True)
    confidence = serializers.FloatField()
    liveness_score = serializers.FloatField()
    is_live = serializers.BooleanField()
    has_mask = serializers.BooleanField()
    face_locations = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))
    anomaly_detected = serializers.BooleanField()


class AttendanceStatsSerializer(serializers.Serializer):
    """Serializer for attendance statistics."""
    total_users = serializers.IntegerField()
    present_today = serializers.IntegerField()
    absent_today = serializers.IntegerField()
    total_attendance_records = serializers.IntegerField()
    anomaly_alerts_today = serializers.IntegerField()
    mask_compliance_rate = serializers.FloatField()
    liveness_success_rate = serializers.FloatField()
