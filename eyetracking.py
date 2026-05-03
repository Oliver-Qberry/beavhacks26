import cv2
import mediapipe as mp
import numpy as np
import os

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from coordinate import Coordinate

# Return the average of two coordinate points
def avg_coords(coord_1: Coordinate, coord_2: Coordinate) -> Coordinate:
    x_avg = (coord_1.x + coord_2.x) / 2
    y_avg = (coord_1.y + coord_2.y) / 2
    return Coordinate(x_avg, y_avg)


# Calculates the Eye Aspect Ratio (EAR) or how open or closed the eye is, using the provided landmarks
def calculate_EAR(landmarks, corners, eyelids) -> float:
    left = landmarks[corners[0]]
    right = landmarks[corners[1]]
    top = landmarks[eyelids[1]]
    bottom = landmarks[eyelids[0]]

    horizontal = ((left.x - right.x) ** 2 + (left.y - right.y) ** 2) ** 0.5
    vertical = ((top.x - bottom.x) ** 2 + (bottom.y- top.y) ** 2) ** 0.5
    return vertical / horizontal

# Converts a landmark's position in to a position on the camera video
def to_pixel(landmark, w, h):
    return int(landmark.x * w), int(landmark.y * h)

# Gets the center of the eye
def get_center(indices, landmarks, w, h):
    points = [to_pixel(landmarks[i], w, h) for i in indices]
    center_x = int(np.mean([p[0] for p in points]))
    center_y = int(np.mean([p[1] for p in points]))
    return center_x, center_y

# Start the calibration sequence
def start_calibration() -> bool:
    print("Starting calibration...")
    print("Please look to the top left")
    return True

# Create the facial landmark detector
def create_detector():
    model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

    base_options = python.BaseOptions(model_asset_path=model_path)

    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1
    )

    return vision.FaceLandmarker.create_from_options(options)

# Create the image from the frame
def create_image(frame):
    # Convert BGR → RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to MediaPipe Image
    return mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

# Use calibration values to determin where the edges of the screen are
def compute_edges(avg_calibration):
    l_edge = ((avg_calibration[0].x) + (avg_calibration[2].x)) / 2
    r_edge = ((avg_calibration[1].x) + avg_calibration[3].x) / 2

    t_edge = (avg_calibration[0].y + avg_calibration[1].y) / 2
    b_edge = (avg_calibration[2].y + avg_calibration[3].y) / 2
    return l_edge, r_edge, t_edge, b_edge
