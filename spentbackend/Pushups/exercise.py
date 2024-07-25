import cv2
import numpy as np
import mediapipe as mp

def calculate_angle(a, b, c):
    a = np.array(a)  # First point
    b = np.array(b)  # Mid point
    c = np.array(c)  # End point
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

class Exercise:
    def __init__(self):
        self.counter = 0
        self.stage = 'up'
        self.feedback = []

    def pushups(self, image: np.ndarray, landmarks: list, reps: int):
        mp_pose = mp.solutions.pose.PoseLandmark
        # Define landmarks
        r1 = [int(landmarks[mp_pose.RIGHT_SHOULDER].x * image.shape[1]), int(landmarks[mp_pose.RIGHT_SHOULDER].y * image.shape[0])]
        r2 = [int(landmarks[mp_pose.RIGHT_ELBOW].x * image.shape[1]), int(landmarks[mp_pose.RIGHT_ELBOW].y * image.shape[0])]
        r3 = [int(landmarks[mp_pose.RIGHT_WRIST].x * image.shape[1]), int(landmarks[mp_pose.RIGHT_WRIST].y * image.shape[0])]
        l1 = [int(landmarks[mp_pose.LEFT_SHOULDER].x * image.shape[1]), int(landmarks[mp_pose.LEFT_SHOULDER].y * image.shape[0])]
        l2 = [int(landmarks[mp_pose.LEFT_ELBOW].x * image.shape[1]), int(landmarks[mp_pose.LEFT_ELBOW].y * image.shape[0])]
        l3 = [int(landmarks[mp_pose.LEFT_WRIST].x * image.shape[1]), int(landmarks[mp_pose.LEFT_WRIST].y * image.shape[0])]
        l4 = [int(landmarks[mp_pose.LEFT_HIP].x * image.shape[1]), int(landmarks[mp_pose.LEFT_HIP].y * image.shape[0])]
        l5 = [int(landmarks[mp_pose.LEFT_KNEE].x * image.shape[1]), int(landmarks[mp_pose.LEFT_KNEE].y * image.shape[0])]
        l6 = [int(landmarks[mp_pose.LEFT_ANKLE].x * image.shape[1]), int(landmarks[mp_pose.LEFT_ANKLE].y * image.shape[0])]
        r4 = [int(landmarks[mp_pose.RIGHT_HIP].x * image.shape[1]), int(landmarks[mp_pose.RIGHT_HIP].y * image.shape[0])]
        r5 = [int(landmarks[mp_pose.RIGHT_KNEE].x * image.shape[1]), int(landmarks[mp_pose.RIGHT_KNEE].y * image.shape[0])]
        r6 = [int(landmarks[mp_pose.RIGHT_ANKLE].x * image.shape[1]), int(landmarks[mp_pose.RIGHT_ANKLE].y * image.shape[0])]
        rpalm = [int(landmarks[mp_pose.RIGHT_PINKY].x * image.shape[1]), int(landmarks[mp_pose.RIGHT_PINKY].y * image.shape[0])]
        lpalm = [int(landmarks[mp_pose.LEFT_PINKY].x * image.shape[1]), int(landmarks[mp_pose.LEFT_PINKY].y * image.shape[0])]

        # Calculate angles
        angleR = calculate_angle(r1, r2, r3)
        angleL = calculate_angle(l1, l2, l3)
        back_angleR = calculate_angle(r1, r4, r5)
        back_angleL = calculate_angle(l1, l4, l5)
        palms_distance = np.linalg.norm(np.array(rpalm) - np.array(lpalm))
        shoulder_diff = abs(r1[1] - l1[1])
        hip_diff = abs(r4[1] - l4[1])
        alignment_threshold = 50

        # Flags and colors
        has_error = False
        if angleR <= 50 or angleL <= 50:
            has_error = True
        if back_angleR <= 120 or back_angleL <= 120:
            has_error = True
        if palms_distance < 50:
            has_error = True
        if shoulder_diff > alignment_threshold or hip_diff > alignment_threshold:
            has_error = True

        # Feedback
        self.feedback = []  # Reset feedback for this frame
        if angleR <= 50 or angleL <= 50:
            self.feedback.append("Keep your arms straight!")
        if back_angleR <= 120 or back_angleL <= 120:
            self.feedback.append("Keep your back straight!")
        if palms_distance < 30:
            self.feedback.append("Keep your palms further apart!")
        if shoulder_diff > alignment_threshold or hip_diff > alignment_threshold:
            self.feedback.append("Align your shoulders and hips horizontally!")

        # Counter logic
        if not has_error:
            if angleL < 90 and angleR < 90 and self.stage == 'up':
                self.counter += 1
                self.stage = 'down'
                self.feedback.append(f"Push-up count: {self.counter}")
            if angleL > 90 and angleR > 90 and self.stage == 'down':
                self.stage = 'up'

        if self.counter >= reps:
            self.feedback.append("Exercise complete!")
            return True

        return False

    def get_feedback(self):
        return "; ".join(self.feedback) if self.feedback else "Good form!"