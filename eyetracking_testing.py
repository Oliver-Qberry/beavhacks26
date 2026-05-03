import cv2
import mediapipe as mp
import numpy as np
import time
import os
import pyautogui

from controls.mouse import left_click, right_click, scroll, move_mouse

from coordinate import Coordinate
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

WINK_THRESHOLD = 0.09


calibrating = False
screen_width, screen_height = pyautogui.size()

left_calibration = []
right_calibration = []

def calculate_EAR(landmarks, p1: int, p2: int, p3: int, p4:int) -> float:
    left = landmarks[p1]
    right = landmarks[p4]
    top = landmarks[p2]
    bottom = landmarks[p3]

    horizontal = ((left.x - right.x) ** 2 + (left.y - right.y) ** 2) ** 0.5
    vertical = ((top.x - bottom.x) ** 2 + (top.y - bottom.y) ** 2) ** 0.5
    return vertical / horizontal

def to_pixel(landmark):
    return int(landmark.x * w), int(landmark.y * h)


def get_center(indices, landmarks):
    points = [to_pixel(landmarks[i]) for i in indices]
    center_x = int(np.mean([p[0] for p in points]))
    center_y = int(np.mean([p[1] for p in points]))
    return center_x, center_y

def start_calibration() -> bool:
    print("Starting calibration...")
    return True

def input_handling(key):
    pass



# --- Load model ---
model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

base_options = python.BaseOptions(model_asset_path=model_path)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)

detector = vision.FaceLandmarker.create_from_options(options)

# --- Webcam ---
CAMERA = 1
cap = cv2.VideoCapture(CAMERA)

if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

# --- Main loop ---
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip for mirror view
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Convert BGR → RGB (IMPORTANT)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to MediaPipe Image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Timestamp in milliseconds
    timestamp = int(time.time() * 1000)

    # Run detection (VIDEO mode)
    result = detector.detect_for_video(mp_image, timestamp)

    # --- Draw landmarks ---
    if result.face_landmarks:
        h, w, _ = frame.shape

        RIGHT_IRIS = [474, 475, 476, 477]
        LEFT_IRIS = [469, 470, 471, 472]
        LEFT_EYE_CORNERS = [33, 133]
        RIGHT_EYE_CORNERS = [362, 263]


        # Full face
        """for landmark in result.face_landmarks[0]:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)"""

        # Edges of left iris
        for landmark in LEFT_IRIS:
            x = int(result.face_landmarks[0][landmark].x * w)
            y = int(result.face_landmarks[0][landmark].y * h)
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # edges of right iris
        for landmark in RIGHT_IRIS:
            x = int(result.face_landmarks[0][landmark].x * w)
            y = int(result.face_landmarks[0][landmark].y * h)
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # corners of the left eye
        for landmark in LEFT_EYE_CORNERS:
            x = int(result.face_landmarks[0][landmark].x * w)
            y = int(result.face_landmarks[0][landmark].y * h)
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # corners of the right eye
        for landmark in RIGHT_EYE_CORNERS:
            x = int(result.face_landmarks[0][landmark].x * w)
            y = int(result.face_landmarks[0][landmark].y * h)
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        #left_iris_center_x, left_iris_center_y = get_center(LEFT_IRIS,result.face_landmarks[0])
        cv2.circle(frame, (get_center(LEFT_IRIS,result.face_landmarks[0])), 1, (0, 255, 0), -1)
        cv2.circle(frame, (get_center(RIGHT_IRIS, result.face_landmarks[0])), 1, (0, 255, 0), -1)

    #if result.face_landmarks[0][159].x - result.face_landmarks[0][145].x <:
    cv2.circle(frame, (int(result.face_landmarks[0][159].x * w), int(result.face_landmarks[0][159].y * h)), 1, (0, 255, 0), -1)
    cv2.circle(frame, (int(result.face_landmarks[0][145].x * w), int(result.face_landmarks[0][145].y * h)), 1, (0, 255, 0), -1)
    #print(f"Left eyelid distance: {result.face_landmarks[0][159].x - result.face_landmarks[0][145].x}")


    # Show window
    cv2.imshow("Face Landmarker", frame)

    if not calibrating and len(left_calibration) == 0:
        print(f"calibrating: {calibrating}")
        calibrating = start_calibration()
    elif len(left_calibration) != 0 and not calibrating:
        left_edge = ((left_calibration[0].x) + (left_calibration[2].x)) / 2
        right_edge = ((left_calibration[1].x) + left_calibration[3].x) / 2

        top_edge = (left_calibration[0].y + left_calibration[1].y) / 2
        bottom_edge = (left_calibration[2].y + left_calibration[3].y) / 2

        left_iris_x, left_iris_y = get_center(LEFT_IRIS,result.face_landmarks[0])
        u = (left_iris_x - left_edge)/ (right_edge - left_edge)
        v = (left_iris_y - top_edge)/ (bottom_edge - top_edge)
        """print("eye_x: ", left_iris_x)
        print("left_edge: ", left_edge)
        print("right_edge: ", right_edge)
        print("u: ", u)"""

        #print(f"x position: {u *screen_width}")
        move_mouse(u * screen_width, v * screen_height)
    left_EAR = calculate_EAR(result.face_landmarks[0], 33, 159, 145, 133)
    right_EAR = calculate_EAR(result.face_landmarks[0], 362, 386, 374, 263)
    #TODO: add bool to not have it continually wink
    if left_EAR < WINK_THRESHOLD < right_EAR:
        print("left wink")
        left_click()
    elif left_EAR > WINK_THRESHOLD > right_EAR:
        print("right wink")
        right_click()


    key = cv2.waitKey(1) & 0xFF
    # Press ESC to quit
    if key == 27:
        break
    elif key == ord("c") and calibrating:
        if result.face_landmarks:
            x, y = get_center(RIGHT_IRIS,result.face_landmarks[0])
            right_calibration.append(Coordinate(x, y))
            left_x, left_y = get_center(LEFT_IRIS,result.face_landmarks[0])
            left_calibration.append(Coordinate(left_x, left_y))
            if len(left_calibration) >= 4:
                calibrating = False
                print("Done calibrating")
                for coordinate in left_calibration:
                    coordinate.print()
                #calculate_calibration()
        else:
            print("Failed that calibration, please try again")

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
