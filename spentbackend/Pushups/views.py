# Pushups/views.py

import cv2
import numpy as np
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .exercise import Exercise
import mediapipe as mp

# Initialize the exercise class
exercise = Exercise()

# Initialize Mediapipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

@api_view(['POST'])
def process_image(request):
    file = request.FILES.get('file')
    contents = file.read()
    np_img = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = pose.process(img_rgb)

    if result.pose_landmarks:
        landmarks = [{'x': lm.x, 'y': lm.y, 'z': lm.z} for lm in result.pose_landmarks.landmark]

        completed = exercise.pushups(img, result.pose_landmarks.landmark, reps=10)
        feedback = exercise.get_feedback()
        count = exercise.counter

        img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing.draw_landmarks(img_rgb, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        _, img_encoded = cv2.imencode('.jpg', img_rgb)
        img_bytes = img_encoded.tobytes()

        return JsonResponse({
            'feedback': feedback,
            'count': count,
            'landmarks': landmarks,
            'image': img_bytes.hex()
        })
    else:
        return JsonResponse({
            'feedback': 'No landmarks detected!',
            'count': exercise.counter,
            'landmarks': [],
            'image': ''
        })
