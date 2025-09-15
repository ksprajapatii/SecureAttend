"""
URL configuration for face recognition app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('recognize/', views.recognize_face_view, name='face-recognize'),
    path('add-face/', views.add_face_encoding_view, name='add-face-encoding'),
    path('test-liveness/', views.test_liveness_view, name='test-liveness'),
]
