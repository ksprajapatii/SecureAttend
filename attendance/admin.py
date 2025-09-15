"""
Admin configuration for attendance models.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, AttendanceRecord, AnomalyAlert, SystemSettings


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['name', 'email', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'email', 'role', 'is_active')
        }),
        ('Face Recognition', {
            'fields': ('photo', 'face_encoding')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'time', 'status', 'mask_status', 'liveness_status', 'anomaly_flag']
    list_filter = ['status', 'mask_status', 'liveness_status', 'anomaly_flag', 'date']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('user', 'date', 'time', 'status')
        }),
        ('Detection Results', {
            'fields': ('mask_status', 'liveness_status', 'confidence_score', 'liveness_score')
        }),
        ('Security', {
            'fields': ('anomaly_flag', 'captured_image', 'ip_address', 'user_agent')
        }),
        ('Additional', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AnomalyAlert)
class AnomalyAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'severity', 'user', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['message', 'user__name']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_type', 'severity', 'message', 'details')
        }),
        ('Related Records', {
            'fields': ('user', 'attendance_record')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'resolved_by')


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Setting', {
            'fields': ('key', 'value', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
