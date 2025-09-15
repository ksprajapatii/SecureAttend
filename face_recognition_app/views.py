"""
Views for face recognition app.
"""
import cv2
import numpy as np
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.files.base import ContentFile
import base64
import logging

from .face_detection import face_detector
from .liveness_detection import liveness_detector
from attendance.models import UserProfile

logger = logging.getLogger('secureattend')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recognize_face_view(request):
    """Standalone face recognition view."""
    try:
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Read image
        image_bytes = image_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return Response(
                {'error': 'Invalid image format'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process image
        results = face_detector.process_image(image)
        
        if not results:
            return Response({
                'faces_detected': 0,
                'recognitions': []
            })
        
        recognitions = []
        for result in results:
            recognition_data = {
                'face_location': result['face_location'],
                'recognition': result['recognition'],
                'mask_detection': result['mask_detection']
            }
            recognitions.append(recognition_data)
        
        return Response({
            'faces_detected': len(results),
            'recognitions': recognitions
        })
        
    except Exception as e:
        logger.error(f"Error in face recognition view: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_face_encoding_view(request):
    """Add face encoding for a user."""
    try:
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        image_file = request.FILES['image']
        
        # Save image temporarily
        temp_path = f'/tmp/temp_face_{user_id}.jpg'
        with open(temp_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)
        
        # Add face encoding
        success = face_detector.add_face_encoding(user_profile, temp_path)
        
        # Clean up temp file
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if success:
            return Response({
                'message': 'Face encoding added successfully',
                'user_id': user_id
            })
        else:
            return Response(
                {'error': 'Failed to add face encoding'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error adding face encoding: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_liveness_view(request):
    """Test liveness detection."""
    try:
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Read image
        image_bytes = image_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return Response(
                {'error': 'Invalid image format'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Detect faces first
        face_locations = face_detector.detect_faces(image)
        
        if not face_locations:
            return Response({
                'faces_detected': 0,
                'liveness_results': []
            })
        
        liveness_results = []
        for face_location in face_locations:
            liveness_result = liveness_detector.detect_liveness(image, face_location)
            liveness_results.append({
                'face_location': face_location,
                'liveness_result': liveness_result
            })
        
        return Response({
            'faces_detected': len(face_locations),
            'liveness_results': liveness_results
        })
        
    except Exception as e:
        logger.error(f"Error in liveness test: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
