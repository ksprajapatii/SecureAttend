"""
Views for the attendance system.
"""
import base64
import cv2
import numpy as np
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q, Avg
from django.core.files.base import ContentFile
import logging

from .models import UserProfile, AttendanceRecord, AnomalyAlert, SystemSettings
from .serializers import (
    UserProfileSerializer, UserProfileCreateSerializer, AttendanceRecordSerializer,
    AttendanceRecordCreateSerializer, AnomalyAlertSerializer, SystemSettingsSerializer,
    FaceRecognitionRequestSerializer, FaceRecognitionResponseSerializer, AttendanceStatsSerializer
)
from face_recognition_app.face_detection import face_detector
from face_recognition_app.liveness_detection import liveness_detector
from .tasks import send_anomaly_alert_email

logger = logging.getLogger('secureattend')


# Dashboard Views
def login_view(request):
    """Login view for the dashboard."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'attendance/login.html')


@login_required
def logout_view(request):
    """Logout view."""
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard view."""
    # Get statistics
    today = date.today()
    
    stats = {
        'total_users': UserProfile.objects.filter(is_active=True).count(),
        'present_today': AttendanceRecord.objects.filter(
            date=today, status='Present'
        ).count(),
        'absent_today': UserProfile.objects.filter(is_active=True).count() - 
                       AttendanceRecord.objects.filter(date=today, status='Present').count(),
        'total_attendance_records': AttendanceRecord.objects.count(),
        'anomaly_alerts_today': AnomalyAlert.objects.filter(
            created_at__date=today, is_resolved=False
        ).count(),
    }
    
    # Calculate mask compliance rate
    mask_records = AttendanceRecord.objects.filter(date=today)
    if mask_records.exists():
        stats['mask_compliance_rate'] = (
            mask_records.filter(mask_status='With Mask').count() / mask_records.count() * 100
        )
    else:
        stats['mask_compliance_rate'] = 0
    
    # Calculate liveness success rate
    liveness_records = AttendanceRecord.objects.filter(date=today)
    if liveness_records.exists():
        stats['liveness_success_rate'] = (
            liveness_records.filter(liveness_status='Live').count() / liveness_records.count() * 100
        )
    else:
        stats['liveness_success_rate'] = 0
    
    # Recent attendance records
    recent_attendance = AttendanceRecord.objects.select_related('user').order_by('-created_at')[:10]
    
    # Recent anomaly alerts
    recent_alerts = AnomalyAlert.objects.select_related('user').filter(
        is_resolved=False
    ).order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_attendance': recent_attendance,
        'recent_alerts': recent_alerts,
    }
    
    return render(request, 'attendance/dashboard.html', context)


@login_required
def users_view(request):
    """Users management view."""
    users = UserProfile.objects.select_related('user').all()
    return render(request, 'attendance/users.html', {'users': users})


@login_required
def attendance_view(request):
    """Attendance records view."""
    # Get filter parameters
    user_id = request.GET.get('user')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Build query
    records = AttendanceRecord.objects.select_related('user').all()
    
    if user_id:
        records = records.filter(user_id=user_id)
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    
    records = records.order_by('-date', '-time')
    
    # Get users for filter dropdown
    users = UserProfile.objects.filter(is_active=True)
    
    context = {
        'records': records,
        'users': users,
        'filters': {
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'attendance/attendance.html', context)


@login_required
def alerts_view(request):
    """Anomaly alerts view."""
    alerts = AnomalyAlert.objects.select_related('user', 'resolved_by').order_by('-created_at')
    return render(request, 'attendance/alerts.html', {'alerts': alerts})


# API Views
class UserProfileListCreateView(generics.ListCreateAPIView):
    """List and create user profiles."""
    queryset = UserProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserProfileCreateSerializer
        return UserProfileSerializer
    
    def get_queryset(self):
        return UserProfile.objects.select_related('user').all()


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user profile."""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttendanceRecordListCreateView(generics.ListCreateAPIView):
    """List and create attendance records."""
    queryset = AttendanceRecord.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AttendanceRecordCreateSerializer
        return AttendanceRecordSerializer
    
    def get_queryset(self):
        queryset = AttendanceRecord.objects.select_related('user').all()
        
        # Filter by user if specified
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.order_by('-date', '-time')


class AttendanceRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an attendance record."""
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


class AnomalyAlertListView(generics.ListAPIView):
    """List anomaly alerts."""
    queryset = AnomalyAlert.objects.all()
    serializer_class = AnomalyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AnomalyAlert.objects.select_related('user', 'resolved_by').all()
        
        # Filter by resolved status
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        return queryset.order_by('-created_at')


class AnomalyAlertDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update an anomaly alert."""
    queryset = AnomalyAlert.objects.all()
    serializer_class = AnomalyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        """Update alert with resolution information."""
        instance = self.get_object()
        instance.is_resolved = request.data.get('is_resolved', instance.is_resolved)
        instance.resolved_by = request.user
        instance.resolved_at = datetime.now()
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def recognize_face(request):
    """Face recognition endpoint."""
    try:
        serializer = FaceRecognitionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = serializer.validated_data['image']
        check_liveness = serializer.validated_data.get('check_liveness', True)
        check_mask = serializer.validated_data.get('check_mask', True)
        
        # Read image
        image_bytes = image_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return Response(
                {'error': 'Invalid image format'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process image for face recognition
        results = face_detector.process_image(image)
        
        if not results:
            return Response({
                'recognized': False,
                'user_id': None,
                'user_name': None,
                'confidence': 0.0,
                'liveness_score': 0.0,
                'is_live': False,
                'has_mask': False,
                'face_locations': [],
                'anomaly_detected': False
            })
        
        # Use the first detected face
        result = results[0]
        recognition = result['recognition']
        mask_detection = result['mask_detection']
        
        # Liveness detection
        liveness_result = {'is_live': True, 'liveness_score': 1.0}
        if check_liveness:
            liveness_result = liveness_detector.detect_liveness(
                image, result['face_location']
            )
        
        # Check for anomalies
        anomaly_detected = False
        if not recognition['recognized']:
            anomaly_detected = True
        elif recognition['confidence'] < 0.7:
            anomaly_detected = True
        elif check_liveness and not liveness_result['is_live']:
            anomaly_detected = True
        
        # Create anomaly alert if needed
        if anomaly_detected:
            alert_type = 'unknown_person'
            if recognition['recognized'] and recognition['confidence'] < 0.7:
                alert_type = 'low_confidence'
            elif check_liveness and not liveness_result['is_live']:
                alert_type = 'spoof_attempt'
            
            # Create alert
            alert = AnomalyAlert.objects.create(
                alert_type=alert_type,
                severity='high' if alert_type == 'spoof_attempt' else 'medium',
                user_id=recognition['user_id'] if recognition['user_id'] else None,
                message=f"Anomaly detected: {alert_type}",
                details={
                    'confidence': recognition['confidence'],
                    'liveness_score': liveness_result['liveness_score'],
                    'has_mask': mask_detection['has_mask'],
                    'face_location': result['face_location']
                }
            )
            
            # Send email alert
            send_anomaly_alert_email.delay(alert.id)
        
        response_data = {
            'recognized': recognition['recognized'],
            'user_id': recognition['user_id'],
            'user_name': recognition['user_name'],
            'confidence': recognition['confidence'],
            'liveness_score': liveness_result['liveness_score'],
            'is_live': liveness_result['is_live'],
            'has_mask': mask_detection['has_mask'],
            'face_locations': [result['face_location']],
            'anomaly_detected': anomaly_detected
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error in face recognition: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_attendance(request):
    """Mark attendance for a recognized user."""
    try:
        user_id = request.data.get('user_id')
        confidence = request.data.get('confidence', 0.0)
        liveness_score = request.data.get('liveness_score', 0.0)
        is_live = request.data.get('is_live', True)
        has_mask = request.data.get('has_mask', False)
        captured_image = request.data.get('captured_image')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_profile = UserProfile.objects.get(id=user_id, is_active=True)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if attendance already marked for today
        today = date.today()
        existing_record = AttendanceRecord.objects.filter(
            user=user_profile, date=today
        ).first()
        
        if existing_record:
            return Response(
                {'error': 'Attendance already marked for today'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine status based on liveness and confidence
        if is_live and confidence > 0.7:
            status = 'Present'
        elif confidence > 0.5:
            status = 'Present'  # Allow with lower confidence but mark as potential issue
        else:
            status = 'Unknown'
        
        # Create attendance record
        attendance_record = AttendanceRecord.objects.create(
            user=user_profile,
            date=today,
            time=datetime.now().time(),
            status=status,
            mask_status='With Mask' if has_mask else 'Without Mask',
            liveness_status='Live' if is_live else 'Spoof',
            confidence_score=confidence,
            liveness_score=liveness_score,
            anomaly_flag=not is_live or confidence < 0.7,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Save captured image if provided
        if captured_image:
            # Decode base64 image
            try:
                format, imgstr = captured_image.split(';base64,')
                ext = format.split('/')[-1]
                image_data = ContentFile(base64.b64decode(imgstr), name=f'attendance_{attendance_record.id}.{ext}')
                attendance_record.captured_image = image_data
                attendance_record.save()
            except Exception as e:
                logger.error(f"Error saving captured image: {e}")
        
        serializer = AttendanceRecordSerializer(attendance_record, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error marking attendance: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_attendance_stats(request):
    """Get attendance statistics."""
    try:
        today = date.today()
        
        stats = {
            'total_users': UserProfile.objects.filter(is_active=True).count(),
            'present_today': AttendanceRecord.objects.filter(
                date=today, status='Present'
            ).count(),
            'absent_today': UserProfile.objects.filter(is_active=True).count() - 
                           AttendanceRecord.objects.filter(date=today, status='Present').count(),
            'total_attendance_records': AttendanceRecord.objects.count(),
            'anomaly_alerts_today': AnomalyAlert.objects.filter(
                created_at__date=today, is_resolved=False
            ).count(),
        }
        
        # Calculate mask compliance rate
        mask_records = AttendanceRecord.objects.filter(date=today)
        if mask_records.exists():
            stats['mask_compliance_rate'] = (
                mask_records.filter(mask_status='With Mask').count() / mask_records.count() * 100
            )
        else:
            stats['mask_compliance_rate'] = 0
        
        # Calculate liveness success rate
        liveness_records = AttendanceRecord.objects.filter(date=today)
        if liveness_records.exists():
            stats['liveness_success_rate'] = (
                liveness_records.filter(liveness_status='Live').count() / liveness_records.count() * 100
            )
        else:
            stats['liveness_success_rate'] = 0
        
        serializer = AttendanceStatsSerializer(stats)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting attendance stats: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
