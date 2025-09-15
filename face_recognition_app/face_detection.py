"""
Face detection and recognition module using OpenCV and face_recognition.
"""
import cv2
import numpy as np
import face_recognition
import os
import pickle
from typing import List, Tuple, Optional, Dict
from django.conf import settings
from attendance.models import UserProfile
import logging

logger = logging.getLogger('secureattend')


class FaceDetector:
    """Face detection and recognition class."""
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known face encodings from database."""
        try:
            profiles = UserProfile.objects.filter(is_active=True, face_encoding__isnull=False)
            for profile in profiles:
                if profile.face_encoding:
                    try:
                        encoding = pickle.loads(profile.face_encoding.encode('latin1'))
                        self.known_face_encodings.append(encoding)
                        self.known_face_names.append(profile.name)
                        self.known_face_ids.append(str(profile.id))
                    except Exception as e:
                        logger.error(f"Error loading face encoding for {profile.name}: {e}")
            
            logger.info(f"Loaded {len(self.known_face_encodings)} known faces")
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in an image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of face locations (top, right, bottom, left)
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face locations
            face_locations = face_recognition.face_locations(
                rgb_image, 
                model=settings.FACE_RECOGNITION_MODEL
            )
            
            return face_locations
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []
    
    def recognize_face(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Dict:
        """
        Recognize a face in the given location.
        
        Args:
            image: Input image as numpy array
            face_location: Face location (top, right, bottom, left)
            
        Returns:
            Dictionary with recognition results
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(rgb_image, [face_location])
            
            if not face_encodings:
                return {
                    'recognized': False,
                    'confidence': 0.0,
                    'user_id': None,
                    'user_name': None
                }
            
            face_encoding = face_encodings[0]
            
            # Compare with known faces
            if self.known_face_encodings:
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                # Use a threshold for recognition
                if face_distances[best_match_index] < 0.6:  # Lower is better
                    confidence = 1 - face_distances[best_match_index]
                    return {
                        'recognized': True,
                        'confidence': confidence,
                        'user_id': self.known_face_ids[best_match_index],
                        'user_name': self.known_face_names[best_match_index]
                    }
            
            return {
                'recognized': False,
                'confidence': 0.0,
                'user_id': None,
                'user_name': None
            }
            
        except Exception as e:
            logger.error(f"Error recognizing face: {e}")
            return {
                'recognized': False,
                'confidence': 0.0,
                'user_id': None,
                'user_name': None
            }
    
    def detect_mask(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Dict:
        """
        Detect if a person is wearing a mask.
        
        Args:
            image: Input image as numpy array
            face_location: Face location (top, right, bottom, left)
            
        Returns:
            Dictionary with mask detection results
        """
        try:
            top, right, bottom, left = face_location
            
            # Extract face region
            face_image = image[top:bottom, left:right]
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV)
            
            # Define range for skin color
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            # Create mask for skin color
            skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # Calculate percentage of skin color in lower half of face
            height, width = face_image.shape[:2]
            lower_half = skin_mask[height//2:, :]
            skin_percentage = np.sum(lower_half > 0) / (lower_half.shape[0] * lower_half.shape[1])
            
            # If skin percentage is low, likely wearing a mask
            has_mask = skin_percentage < 0.3
            
            return {
                'has_mask': has_mask,
                'confidence': 1 - skin_percentage if has_mask else skin_percentage,
                'skin_percentage': skin_percentage
            }
            
        except Exception as e:
            logger.error(f"Error detecting mask: {e}")
            return {
                'has_mask': False,
                'confidence': 0.0,
                'skin_percentage': 0.0
            }
    
    def process_image(self, image: np.ndarray) -> List[Dict]:
        """
        Process an image to detect faces, recognize them, and check for masks.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of dictionaries with detection results for each face
        """
        results = []
        
        # Detect faces
        face_locations = self.detect_faces(image)
        
        for face_location in face_locations:
            # Recognize face
            recognition_result = self.recognize_face(image, face_location)
            
            # Detect mask
            mask_result = self.detect_mask(image, face_location)
            
            # Combine results
            result = {
                'face_location': face_location,
                'recognition': recognition_result,
                'mask_detection': mask_result
            }
            
            results.append(result)
        
        return results
    
    def add_face_encoding(self, user_profile: UserProfile, image_path: str) -> bool:
        """
        Add a new face encoding to the system.
        
        Args:
            user_profile: UserProfile instance
            image_path: Path to the image file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                logger.warning(f"No face found in image for {user_profile.name}")
                return False
            
            # Get face encoding (use the first face found)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if not face_encodings:
                logger.warning(f"Could not encode face for {user_profile.name}")
                return False
            
            # Store encoding
            encoding_str = pickle.dumps(face_encodings[0]).decode('latin1')
            user_profile.face_encoding = encoding_str
            user_profile.save()
            
            # Reload known faces
            self.load_known_faces()
            
            logger.info(f"Successfully added face encoding for {user_profile.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding face encoding for {user_profile.name}: {e}")
            return False


# Global face detector instance
face_detector = FaceDetector()
