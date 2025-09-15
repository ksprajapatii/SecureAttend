"""
URL configuration for attendance app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs
urlpatterns = [
    # User Profile APIs
    path('users/', views.UserProfileListCreateView.as_view(), name='user-list-create'),
    path('users/<uuid:pk>/', views.UserProfileDetailView.as_view(), name='user-detail'),
    
    # Attendance Record APIs
    path('attendance/', views.AttendanceRecordListCreateView.as_view(), name='attendance-list-create'),
    path('attendance/<uuid:pk>/', views.AttendanceRecordDetailView.as_view(), name='attendance-detail'),
    
    # Anomaly Alert APIs
    path('alerts/', views.AnomalyAlertListView.as_view(), name='alert-list'),
    path('alerts/<uuid:pk>/', views.AnomalyAlertDetailView.as_view(), name='alert-detail'),
    
    # Face Recognition APIs
    path('recognize-face/', views.recognize_face, name='recognize-face'),
    path('mark-attendance/', views.mark_attendance, name='mark-attendance'),
    
    # Statistics API
    path('stats/', views.get_attendance_stats, name='attendance-stats'),
]
