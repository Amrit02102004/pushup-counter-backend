# src/calculateAngle.py

import math
import numpy as np

def calculate_angle(a, b, c):
    # Calculate the angle between three points
    a = np.array(a)  # First point
    b = np.array(b)  # Midpoint
    c = np.array(c)  # End point

    # Vector AB and BC
    ab = a - b
    bc = c - b

    # Dot product and magnitudes
    dot_product = np.dot(ab, bc)
    magnitude_ab = np.linalg.norm(ab)
    magnitude_bc = np.linalg.norm(bc)

    # Angle in degrees
    angle = np.arccos(dot_product / (magnitude_ab * magnitude_bc))  # Radians
    angle = np.degrees(angle)  # Convert to degrees
    return angle
