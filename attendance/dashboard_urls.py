"""
Dashboard URL configuration for attendance app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.users_view, name='users'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('alerts/', views.alerts_view, name='alerts'),
]
