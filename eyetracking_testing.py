import cv2
import mediapipe as mp
import numpy as np
import time
import os
import pyautogui

from flags import Flags
from controls.mouse import left_click, right_click, scroll, move_mouse

from coordinate import Coordinate
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ------Camera to use-----
# 0 for iphone camera, 1 for laptop webcam
CAMERA = 1

WINK_THRESHOLD = .09
WINK_FRAMES_REQUIRED = 2

# -----Eye landmarks -----
RIGHT_IRIS = [474, 475, 476, 477]
LEFT_IRIS = [469, 470, 471, 472]
LEFT_EYE_CORNERS = [33, 133]
RIGHT_EYE_CORNERS = [362, 263]

EYE_MARKERS = [RIGHT_IRIS, LEFT_IRIS, LEFT_EYE_CORNERS, RIGHT_EYE_CORNERS]

# -----Screen size-----
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()


SMOOTHING = 0.5

# -----Calibration-----
DIRECTIONS = ["top left", "top right", "bottom left", "bottom right"]

left_calibration = []
right_calibration = []
avg_calibration = []


def avg_coords(coord_1: Coordinate, coord_2: Coordinate) -> Coordinate:
    x_avg = (coord_1.x + coord_2.x) / 2
    y_avg = (coord_1.y + coord_2.y) / 2
    return Coordinate(x_avg, y_avg)


# Calculates the Eye Aspect Ratio (EAR) or how open or closed the eye is, using the provided landmarks
def calculate_EAR(landmarks, p1: int, p2: int, p3: int, p4:int) -> float:
    left = landmarks[p1]
    right = landmarks[p4]
    top = landmarks[p2]
    bottom = landmarks[p3]

    horizontal = ((left.x - right.x) ** 2 + (left.y - right.y) ** 2) ** 0.5
    vertical = ((top.x - bottom.x) ** 2 + (top.y - bottom.y) ** 2) ** 0.5
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

def start_calibration() -> bool:
    print("Starting calibration...")
    print(f"Please look to the {DIRECTIONS[0]}")
    return True

# Does absolutely nothing because I don't feel like dealing with all the variables that need to be passed around
def input_handling(key):
    pass

def create_detector():
    model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

    base_options = python.BaseOptions(model_asset_path=model_path)

    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1
    )

    return vision.FaceLandmarker.create_from_options(options)

def create_image(frame):
    # Convert BGR → RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to MediaPipe Image
    return mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

def main() -> None:
    prev_x, prev_y = 0, 0
    flags = Flags()

    # --- Load model ---
    detector = create_detector()
    print(type(detector))

    # --- Webcam ---
    cap = cv2.VideoCapture(CAMERA)

    if not cap.isOpened():
        print("Error: Could not open webcam")
        exit()

    flags.calibrating = start_calibration()

    # --- Main loop ---
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip for mirror view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Timestamp in milliseconds
        timestamp = int(time.time() * 1000)

        # Run detection
        result = detector.detect_for_video(create_image(frame), timestamp)

        # --- Draw landmarks ---
        if result.face_landmarks:
            h, w, _ = frame.shape

            # Full face
            """for landmark in result.face_landmarks[0]:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)"""

            for l in EYE_MARKERS:
                for landmark in l:
                    x = int(result.face_landmarks[0][landmark].x * w)
                    y = int(result.face_landmarks[0][landmark].y * h)
                    cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

            # Markers for individual marker lists for debugging
            """# Edges of left iris
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
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)"""

            #center of eyes
            cv2.circle(frame, (get_center(LEFT_IRIS,result.face_landmarks[0], w, h)), 1, (0, 255, 0), -1)
            cv2.circle(frame, (get_center(RIGHT_IRIS, result.face_landmarks[0], w, h)), 1, (0, 255, 0), -1)

            # left eyelid points
            #cv2.circle(frame, (int(result.face_landmarks[0][159].x * w), int(result.face_landmarks[0][159].y * h)), 1, (0, 255, 0), -1)
            #cv2.circle(frame, (int(result.face_landmarks[0][145].x * w), int(result.face_landmarks[0][145].y * h)), 1, (0, 255, 0), -1)


        # Show window
        cv2.imshow("Face Landmarker", frame)

        # Convert eye position to screen position
        if not flags.calibrating and len(avg_calibration) == 0:
            print(f"calibrating: {flags.calibrating}")
        elif len(avg_calibration) != 0 and not flags.calibrating:
            left_edge = ((avg_calibration[0].x) + (avg_calibration[2].x)) / 2
            right_edge = ((avg_calibration[1].x) + avg_calibration[3].x) / 2

            top_edge = (avg_calibration[0].y + avg_calibration[1].y) / 2
            bottom_edge = (avg_calibration[2].y + avg_calibration[3].y) / 2

            lx, ly = get_center(LEFT_IRIS,result.face_landmarks[0], w, h)
            rx, ry = get_center(RIGHT_IRIS,result.face_landmarks[0], w, h)
            u = ((lx + rx) / 2 - left_edge) / (right_edge - left_edge)
            v = ((ly + ry) / 2 - top_edge) / (bottom_edge - top_edge)
            # Clamp values
            u = max(0, min(1, u))
            v = max(0, min(1, v))

            target_x = u * SCREEN_WIDTH
            target_y = v * SCREEN_HEIGHT

            smooth_x = SMOOTHING * target_x + (1-SMOOTHING) * prev_x
            smooth_y = SMOOTHING * target_y + (1-SMOOTHING) * prev_y
            prev_x, prev_y = smooth_x, smooth_y

            left_EAR = calculate_EAR(result.face_landmarks[0], 33, 159, 145, 133)
            right_EAR = calculate_EAR(result.face_landmarks[0], 362, 386, 374, 263)
            both_closed = left_EAR < WINK_THRESHOLD and right_EAR < WINK_THRESHOLD
            if not both_closed: # Dont moving during blinking
                move_mouse(smooth_x, smooth_y)
        #TODO: this if statement is redundant
        if result.face_landmarks:
            left_EAR = calculate_EAR(result.face_landmarks[0], 33, 159, 145, 133)
            right_EAR = calculate_EAR(result.face_landmarks[0], 362, 386, 374, 263)
            #FIXME: flag resets if you open one eye
            if left_EAR < WINK_THRESHOLD < right_EAR:
                flags.wink_frames += 1
                if flags.wink_frames == WINK_FRAMES_REQUIRED:
                    print("left wink")
                    left_click()
            elif left_EAR > WINK_THRESHOLD > right_EAR:
                flags.right_wink_frames += 1
                if flags.right_wink_frames == WINK_FRAMES_REQUIRED:
                    print("right wink")
                    right_click()
            else:
                flags.wink_frames = 0
                flags.right_wink_frames = 0


        key = cv2.waitKey(1) & 0xFF
        # Press ESC to quit
        if key == 27:
            break
        elif key == ord("c") and flags.calibrating:
            if result.face_landmarks:
                x, y = get_center(RIGHT_IRIS,result.face_landmarks[0], w, h)
                right_cord = Coordinate(x, y)
                right_calibration.append(right_cord)
                left_x, left_y = get_center(LEFT_IRIS,result.face_landmarks[0],w, h)
                left_cord = Coordinate(left_x, left_y)
                left_calibration.append(left_cord)
                avg_calibration.append(avg_coords(left_cord, right_cord))
                if len(avg_calibration) >= 4:
                    flags.calibrating = False
                    print("Done calibrating")
                    """for coordinate in left_calibration:
                        coordinate.print()"""
                else:
                    print(f"And now please look to the {DIRECTIONS[len(avg_calibration)]}")
            else:
                print("Failed that calibration, please try again")

    # --- Cleanup ---
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    """try:
        main()
    except Exception as e:
        print("Error: {}".format(e))"""