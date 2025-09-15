"""
Liveness detection module to prevent spoofing attacks.
"""
import cv2
import numpy as np
import dlib
from typing import Dict, List, Tuple
import logging
from django.conf import settings

logger = logging.getLogger('secureattend')


class LivenessDetector:
    """Liveness detection using eye aspect ratio and head pose estimation."""
    
    def __init__(self):
        self.predictor_path = None
        self.detector = None
        self.predictor = None
        self.ear_threshold = settings.BLINK_THRESHOLD
        self.head_pose_threshold = settings.HEAD_POSE_THRESHOLD
        
        # Initialize face detector and landmark predictor
        self._initialize_models()
        
        # Eye aspect ratio calculation constants
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES = 3
        
        # Blink detection state
        self.blink_counter = 0
        self.total_blinks = 0
        self.ear_history = []
        
    def _initialize_models(self):
        """Initialize dlib models for face detection and landmark prediction."""
        try:
            # Try to use dlib's built-in face detector
            self.detector = dlib.get_frontal_face_detector()
            
            # Try to download and use the shape predictor
            try:
                import urllib.request
                import os
                
                predictor_url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
                predictor_path = "shape_predictor_68_face_landmarks.dat"
                
                if not os.path.exists(predictor_path):
                    logger.info("Downloading face landmark predictor...")
                    urllib.request.urlretrieve(predictor_url, predictor_path + ".bz2")
                    
                    # Decompress the file
                    import bz2
                    with bz2.BZ2File(predictor_path + ".bz2", 'rb') as source:
                        with open(predictor_path, 'wb') as target:
                            target.write(source.read())
                    
                    os.remove(predictor_path + ".bz2")
                
                self.predictor = dlib.shape_predictor(predictor_path)
                logger.info("Successfully initialized liveness detection models")
                
            except Exception as e:
                logger.warning(f"Could not initialize landmark predictor: {e}")
                self.predictor = None
                
        except Exception as e:
            logger.error(f"Error initializing liveness detection models: {e}")
            self.detector = None
            self.predictor = None
    
    def eye_aspect_ratio(self, eye_landmarks: np.ndarray) -> float:
        """
        Calculate the Eye Aspect Ratio (EAR).
        
        Args:
            eye_landmarks: Array of eye landmark coordinates
            
        Returns:
            Eye aspect ratio value
        """
        try:
            # Calculate distances
            A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
            B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
            C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
            
            # Calculate EAR
            ear = (A + B) / (2.0 * C)
            return ear
            
        except Exception as e:
            logger.error(f"Error calculating EAR: {e}")
            return 0.0
    
    def get_eye_landmarks(self, landmarks: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract left and right eye landmarks.
        
        Args:
            landmarks: Full face landmarks (68 points)
            
        Returns:
            Tuple of (left_eye, right_eye) landmarks
        """
        try:
            # Left eye landmarks (36-41)
            left_eye = landmarks[36:42]
            # Right eye landmarks (42-47)
            right_eye = landmarks[42:48]
            
            return left_eye, right_eye
            
        except Exception as e:
            logger.error(f"Error extracting eye landmarks: {e}")
            return np.array([]), np.array([])
    
    def detect_blink(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Dict:
        """
        Detect blinks in the face region.
        
        Args:
            image: Input image
            face_location: Face location (top, right, bottom, left)
            
        Returns:
            Dictionary with blink detection results
        """
        try:
            if self.predictor is None:
                return {
                    'blink_detected': False,
                    'ear': 0.0,
                    'total_blinks': 0,
                    'confidence': 0.0
                }
            
            top, right, bottom, left = face_location
            
            # Convert to dlib rectangle
            rect = dlib.rectangle(left, top, right, bottom)
            
            # Get landmarks
            landmarks = self.predictor(image, rect)
            landmarks = np.array([[p.x, p.y] for p in landmarks.parts()])
            
            # Get eye landmarks
            left_eye, right_eye = self.get_eye_landmarks(landmarks)
            
            if left_eye.size == 0 or right_eye.size == 0:
                return {
                    'blink_detected': False,
                    'ear': 0.0,
                    'total_blinks': 0,
                    'confidence': 0.0
                }
            
            # Calculate EAR for both eyes
            left_ear = self.eye_aspect_ratio(left_eye)
            right_ear = self.eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            # Add to history
            self.ear_history.append(ear)
            if len(self.ear_history) > 10:  # Keep only last 10 frames
                self.ear_history.pop(0)
            
            # Detect blink
            blink_detected = False
            if ear < self.EYE_AR_THRESH:
                self.blink_counter += 1
            else:
                if self.blink_counter >= self.EYE_AR_CONSEC_FRAMES:
                    self.total_blinks += 1
                    blink_detected = True
                self.blink_counter = 0
            
            # Calculate confidence based on blink pattern
            confidence = min(1.0, self.total_blinks / 3.0)  # Max confidence after 3 blinks
            
            return {
                'blink_detected': blink_detected,
                'ear': ear,
                'total_blinks': self.total_blinks,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error detecting blink: {e}")
            return {
                'blink_detected': False,
                'ear': 0.0,
                'total_blinks': 0,
                'confidence': 0.0
            }
    
    def estimate_head_pose(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Dict:
        """
        Estimate head pose to detect movement.
        
        Args:
            image: Input image
            face_location: Face location (top, right, bottom, left)
            
        Returns:
            Dictionary with head pose estimation results
        """
        try:
            if self.predictor is None:
                return {
                    'yaw': 0.0,
                    'pitch': 0.0,
                    'roll': 0.0,
                    'movement_detected': False,
                    'confidence': 0.0
                }
            
            top, right, bottom, left = face_location
            
            # Convert to dlib rectangle
            rect = dlib.rectangle(left, top, right, bottom)
            
            # Get landmarks
            landmarks = self.predictor(image, rect)
            landmarks = np.array([[p.x, p.y] for p in landmarks.parts()])
            
            # 3D model points (approximate)
            model_points = np.array([
                (0.0, 0.0, 0.0),             # Nose tip
                (0.0, -330.0, -65.0),        # Chin
                (-225.0, 170.0, -135.0),     # Left eye left corner
                (225.0, 170.0, -135.0),      # Right eye right corner
                (-150.0, -150.0, -125.0),    # Left mouth corner
                (150.0, -150.0, -125.0)      # Right mouth corner
            ])
            
            # 2D image points (from landmarks)
            image_points = np.array([
                landmarks[30],  # Nose tip
                landmarks[8],   # Chin
                landmarks[36],  # Left eye left corner
                landmarks[45],  # Right eye right corner
                landmarks[48],  # Left mouth corner
                landmarks[54]   # Right mouth corner
            ], dtype="double")
            
            # Camera matrix (approximate)
            size = image.shape
            focal_length = size[1]
            center = (size[1]/2, size[0]/2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="double")
            
            # Distortion coefficients (assume no distortion)
            dist_coeffs = np.zeros((4,1))
            
            # Solve PnP
            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_UPNP
            )
            
            if success:
                # Convert rotation vector to rotation matrix
                rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                
                # Extract Euler angles
                yaw, pitch, roll = self.rotation_matrix_to_euler_angles(rotation_matrix)
                
                # Convert to degrees
                yaw = np.degrees(yaw)
                pitch = np.degrees(pitch)
                roll = np.degrees(roll)
                
                # Detect movement (simple threshold-based)
                movement_detected = (abs(yaw) > self.head_pose_threshold or 
                                   abs(pitch) > self.head_pose_threshold or 
                                   abs(roll) > self.head_pose_threshold)
                
                # Calculate confidence based on pose variation
                pose_variation = (abs(yaw) + abs(pitch) + abs(roll)) / 3.0
                confidence = min(1.0, pose_variation / 45.0)  # Max confidence at 45 degrees
                
                return {
                    'yaw': yaw,
                    'pitch': pitch,
                    'roll': roll,
                    'movement_detected': movement_detected,
                    'confidence': confidence
                }
            else:
                return {
                    'yaw': 0.0,
                    'pitch': 0.0,
                    'roll': 0.0,
                    'movement_detected': False,
                    'confidence': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error estimating head pose: {e}")
            return {
                'yaw': 0.0,
                'pitch': 0.0,
                'roll': 0.0,
                'movement_detected': False,
                'confidence': 0.0
            }
    
    def rotation_matrix_to_euler_angles(self, R: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert rotation matrix to Euler angles.
        
        Args:
            R: Rotation matrix
            
        Returns:
            Tuple of (yaw, pitch, roll) in radians
        """
        try:
            sy = np.sqrt(R[0,0] * R[0,0] + R[1,0] * R[1,0])
            
            singular = sy < 1e-6
            
            if not singular:
                x = np.arctan2(R[2,1], R[2,2])
                y = np.arctan2(-R[2,0], sy)
                z = np.arctan2(R[1,0], R[0,0])
            else:
                x = np.arctan2(-R[1,2], R[1,1])
                y = np.arctan2(-R[2,0], sy)
                z = 0
            
            return x, y, z
            
        except Exception as e:
            logger.error(f"Error converting rotation matrix: {e}")
            return 0.0, 0.0, 0.0
    
    def detect_liveness(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Dict:
        """
        Comprehensive liveness detection combining multiple methods.
        
        Args:
            image: Input image
            face_location: Face location (top, right, bottom, left)
            
        Returns:
            Dictionary with liveness detection results
        """
        try:
            # Detect blinks
            blink_result = self.detect_blink(image, face_location)
            
            # Estimate head pose
            pose_result = self.estimate_head_pose(image, face_location)
            
            # Combine results
            blink_confidence = blink_result['confidence']
            pose_confidence = pose_result['confidence']
            
            # Overall liveness score
            liveness_score = (blink_confidence * 0.6 + pose_confidence * 0.4)
            
            # Determine if live based on combined evidence
            is_live = (blink_result['total_blinks'] > 0 or 
                      pose_result['movement_detected'] or 
                      liveness_score > settings.LIVENESS_THRESHOLD)
            
            return {
                'is_live': is_live,
                'liveness_score': liveness_score,
                'blink_result': blink_result,
                'pose_result': pose_result,
                'confidence': liveness_score
            }
            
        except Exception as e:
            logger.error(f"Error in liveness detection: {e}")
            return {
                'is_live': False,
                'liveness_score': 0.0,
                'blink_result': {'confidence': 0.0},
                'pose_result': {'confidence': 0.0},
                'confidence': 0.0
            }
    
    def reset_state(self):
        """Reset the liveness detection state."""
        self.blink_counter = 0
        self.total_blinks = 0
        self.ear_history = []


# Global liveness detector instance
liveness_detector = LivenessDetector()
