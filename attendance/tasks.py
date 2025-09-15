"""
Celery tasks for the attendance system.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import AnomalyAlert, UserProfile
import logging

logger = logging.getLogger('secureattend')


@shared_task
def send_anomaly_alert_email(alert_id):
    """
    Send email alert for anomaly detection.
    
    Args:
        alert_id: ID of the AnomalyAlert instance
    """
    try:
        alert = AnomalyAlert.objects.get(id=alert_id)
        
        # Prepare email content
        subject = f"SecureAttend Alert: {alert.get_alert_type_display()}"
        
        context = {
            'alert': alert,
            'site_name': 'SecureAttend',
        }
        
        # Render email template
        html_message = render_to_string('emails/anomaly_alert.html', context)
        plain_message = f"""
        Alert Type: {alert.get_alert_type_display()}
        Severity: {alert.get_severity_display()}
        Message: {alert.message}
        Time: {alert.created_at}
        User: {alert.user.name if alert.user else 'Unknown'}
        """
        
        # Get admin users
        admin_users = UserProfile.objects.filter(role='admin', is_active=True)
        recipient_list = [user.email for user in admin_users]
        
        if recipient_list:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Anomaly alert email sent for alert {alert_id}")
        else:
            logger.warning(f"No admin users found to send alert email for alert {alert_id}")
            
    except AnomalyAlert.DoesNotExist:
        logger.error(f"AnomalyAlert with id {alert_id} not found")
    except Exception as e:
        logger.error(f"Error sending anomaly alert email: {e}")


@shared_task
def send_daily_attendance_report():
    """
    Send daily attendance report to admin users.
    """
    try:
        from datetime import date
        from django.db.models import Count, Q
        
        today = date.today()
        
        # Get attendance statistics
        total_users = UserProfile.objects.filter(is_active=True).count()
        present_today = AttendanceRecord.objects.filter(
            date=today, status='Present'
        ).count()
        absent_today = total_users - present_today
        anomaly_alerts = AnomalyAlert.objects.filter(
            created_at__date=today, is_resolved=False
        ).count()
        
        # Calculate mask compliance
        mask_records = AttendanceRecord.objects.filter(date=today)
        mask_compliance = 0
        if mask_records.exists():
            mask_compliance = (
                mask_records.filter(mask_status='With Mask').count() / 
                mask_records.count() * 100
            )
        
        # Calculate liveness success rate
        liveness_success = 0
        if mask_records.exists():
            liveness_success = (
                mask_records.filter(liveness_status='Live').count() / 
                mask_records.count() * 100
            )
        
        context = {
            'date': today,
            'total_users': total_users,
            'present_today': present_today,
            'absent_today': absent_today,
            'anomaly_alerts': anomaly_alerts,
            'mask_compliance': mask_compliance,
            'liveness_success': liveness_success,
            'site_name': 'SecureAttend',
        }
        
        subject = f"Daily Attendance Report - {today}"
        
        html_message = render_to_string('emails/daily_report.html', context)
        plain_message = f"""
        Daily Attendance Report - {today}
        
        Total Users: {total_users}
        Present Today: {present_today}
        Absent Today: {absent_today}
        Anomaly Alerts: {anomaly_alerts}
        Mask Compliance: {mask_compliance:.1f}%
        Liveness Success Rate: {liveness_success:.1f}%
        """
        
        # Get admin users
        admin_users = UserProfile.objects.filter(role='admin', is_active=True)
        recipient_list = [user.email for user in admin_users]
        
        if recipient_list:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Daily attendance report sent for {today}")
        else:
            logger.warning(f"No admin users found to send daily report for {today}")
            
    except Exception as e:
        logger.error(f"Error sending daily attendance report: {e}")


@shared_task
def cleanup_old_records():
    """
    Clean up old attendance records and alerts.
    """
    try:
        from datetime import date, timedelta
        
        # Delete attendance records older than 1 year
        cutoff_date = date.today() - timedelta(days=365)
        old_records = AttendanceRecord.objects.filter(date__lt=cutoff_date)
        deleted_records = old_records.count()
        old_records.delete()
        
        # Delete resolved alerts older than 6 months
        cutoff_date = date.today() - timedelta(days=180)
        old_alerts = AnomalyAlert.objects.filter(
            is_resolved=True, 
            resolved_at__date__lt=cutoff_date
        )
        deleted_alerts = old_alerts.count()
        old_alerts.delete()
        
        logger.info(f"Cleanup completed: {deleted_records} records and {deleted_alerts} alerts deleted")
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")


@shared_task
def process_face_encoding_batch():
    """
    Process face encodings for users who don't have them yet.
    """
    try:
        users_without_encoding = UserProfile.objects.filter(
            is_active=True,
            face_encoding__isnull=True,
            photo__isnull=False
        )
        
        processed_count = 0
        for user in users_without_encoding:
            try:
                if user.photo:
                    success = face_detector.add_face_encoding(user, user.photo.path)
                    if success:
                        processed_count += 1
            except Exception as e:
                logger.error(f"Error processing face encoding for user {user.id}: {e}")
        
        logger.info(f"Processed {processed_count} face encodings")
        
    except Exception as e:
        logger.error(f"Error in face encoding batch processing: {e}")
