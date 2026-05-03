# Used for eye tracking
import cv2
import time
import pyautogui

# Our custom modules
from flags import Flags
import controls.mouse as io
from coordinate import Coordinate
from speech import debug_print, interpret_command, interpret_keyboard
from eyetracking import get_center, compute_edges, create_image, create_detector, start_calibration, calculate_EAR, avg_coords

# Use for speech commands
import speech_recognition as sr
import threading
import queue
import string

# Future improvements
# More verbal commands
# Track head to better stabilize mouse movement and remove need for calibration
# Make calibration a verbal command option
# Add audio feedback


#TODO - eyetracking:
# dampen effect of eye movement?
#   - GET IT TO BE MORE ACCURATE
# dont recalculate edges every frame

#TODO - voice commands:
# add a command that does calibration
# "space" was doing a backspace
# add arrow keys

#TODO:
# audio feedback - everything we're printing have it speak?
# better output to the terminal - especially for voice


# ------Camera to use-----
# 0 for iphone camera, 1 for laptop webcam
# If you get "Error: Could not open webcam"
# Switch CAMERA to 0
CAMERA = 1

WINK_THRESHOLD = .07
WINK_FRAMES_REQUIRED = 2

SMOOTHING = 0.3

COMMANDS_PER_FRAME = 3

# -----Eye landmarks -----
RIGHT_IRIS = [474, 475, 476, 477]
LEFT_IRIS = [469, 470, 471, 472]
LEFT_EYE_CORNERS = [33, 133]
RIGHT_EYE_CORNERS = [362, 263]
LEFT_EYE_LIDS = [145, 159] # bottom, top
RIGHT_EYE_LIDS = [374, 386]

EYE_MARKERS = [RIGHT_IRIS, LEFT_IRIS, LEFT_EYE_CORNERS, RIGHT_EYE_CORNERS, LEFT_EYE_LIDS, RIGHT_EYE_LIDS]

# -----Screen size-----
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
pyautogui.FAILSAFE = False


# -----Calibration-----
DIRECTIONS = ["top left", "top right", "bottom left", "bottom right"]
avg_calibration = []
right_calibration = []
left_calibration = []


# Round value to nearest multiple of 5
def round_to_5(value: float) -> float:
    return round(value / 5) * 5

# Smooth out position mouse is moving towards
def smooth(u, v, prev_x, prev_y):
    u = max(0, min(1, u))
    v = max(0, min(1, v))

    target_x = round(u * SCREEN_WIDTH)
    target_y = round(v * SCREEN_HEIGHT)

    smooth_x = round_to_5(SMOOTHING * target_x + (1 - SMOOTHING) * prev_x)
    smooth_y = round_to_5(SMOOTHING * target_y + (1 - SMOOTHING) * prev_y)
    return smooth_x, smooth_y

# Calculate the smoothed mouse position using both eyes
def calculate_smoothed_position(landmarks, previous_x, previous_y, w, h):
    left_edge, right_edge, top_edge, bottom_edge = compute_edges(avg_calibration)

    lx, ly = get_center(LEFT_IRIS, landmarks[0], w, h)
    rx, ry = get_center(RIGHT_IRIS, landmarks[0], w, h)
    u = ((lx + rx) / 2 - left_edge) / (right_edge - left_edge)
    v = ((ly + ry) / 2 - top_edge) / (bottom_edge - top_edge)

    return smooth(u, v, previous_x, previous_y)

# Calculate smoothed mouse position using the left eye
def calculate_left_smoothed_position(landmarks, previous_x, previous_y, w, h):
    left_edge, right_edge, top_edge, bottom_edge = compute_edges(left_calibration)

    lx, ly = get_center(LEFT_IRIS, landmarks[0], w, h)

    u = (lx - left_edge) / (right_edge - left_edge)
    v = (ly - top_edge) / (bottom_edge - top_edge)

    return smooth(u,v,previous_x,previous_y)

# Calculate smoothed mouse position using the right eye
def calculate_right_smoothed_position(landmarks, previous_x, previous_y, w, h):
    left_edge, right_edge, top_edge, bottom_edge = compute_edges(right_calibration)

    rx, ry = get_center(RIGHT_IRIS, landmarks[0], w, h)
    u = (rx - left_edge) / (right_edge - left_edge)
    v = (ry - top_edge) / (bottom_edge - top_edge)

    return smooth(u,v,previous_x,previous_y)

# Main loop for getting verbal commands
def speech_loop(f: Flags, c_queue) -> None:
    command = ""
    r = sr.Recognizer()
    r.energy_threshold = 1000  # Cull out some ambient noise
    mic = sr.Microphone()
    with mic as source:
        # r.adjust_for_ambient_noise(source, duration = 0.1)
        while not f.end_loop:

            if f.keyboard:
                print("Say something to type")
            else:
                print("Give command")
            audio = r.listen(source)

            if not f.keyboard:
                debug_print("Heard! interpreting...")
            try:
                # command = r.recognize_whisper(audio, language="english")
                # command = r.recognize_faster_whisper(audio, language="english")
                # command = r.recognize_sphinx(audio)
                command = r.recognize_google(audio)
                if not f.keyboard:
                    command = command.strip().lower()
                    if command == "":
                        continue
                    command = "".join(filter(lambda x: x not in string.punctuation, command))
                    c_queue.put(command)
                    #interpret_command(command, f)
                else:
                    c_queue.put(command)
                    #interpret_keyboard(command, f)
                print("Command: ", command)

            except sr.UnknownValueError:
                print("Didn't get that. Could you say it again?")
            except sr.RequestError as e:
                print(f"Error: {e}")
    return


def main() -> None:
    flags = Flags()

    command_queue = queue.Queue()

    speech_thread = threading.Thread(
        target=speech_loop,
        args=(flags, command_queue),
        daemon=True
    )

    prev_x, prev_y = 0, 0

    # --- Load model ---
    detector = create_detector()

    # --- Webcam ---
    cap = cv2.VideoCapture(CAMERA)

    if not cap.isOpened():
        # If you get this, try switching CAMERA to be 0
        print("Error: Could not open webcam")
        exit()

    # Start calibration
    flags.calibrating = start_calibration()

    started_speech_thread = False
    # --- Main loop ---
    while not flags.end_loop:
        # -----Handle voice commands-----
        # Start getting verbal input after calibration has happened
        if not flags.calibrating and not started_speech_thread:
            speech_thread.start()
            started_speech_thread = True

        # Process commands in the queue
        for _ in range(COMMANDS_PER_FRAME): # limit commands per frame
            if command_queue.empty():
                break
            command = command_queue.get()
            if not flags.keyboard:
                interpret_command(command, flags)
            else:
                interpret_keyboard(command, flags)


        # -----VISION TRACKING-----
        ret, frame = cap.read()
        if not ret:
            break

        # Flip for mirror view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Timestamp
        timestamp = int(time.time() * 1000)

        # Run detection
        result = detector.detect_for_video(create_image(frame), timestamp)

        if result.face_landmarks:
            # --- Draw landmarks ---

            # Full face
            """for landmark in result.face_landmarks[0]:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)"""

            # Main eye landmarks
            for l in EYE_MARKERS:
                for landmark in l:
                    x = int(result.face_landmarks[0][landmark].x * w)
                    y = int(result.face_landmarks[0][landmark].y * h)
                    cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

            # Center of eyes
            cv2.circle(frame, (get_center(LEFT_IRIS,result.face_landmarks[0], w, h)), 1, (0, 255, 0), -1)
            cv2.circle(frame, (get_center(RIGHT_IRIS, result.face_landmarks[0], w, h)), 1, (0, 255, 0), -1)

            # Eye aspect ratio to see if eyes are closed
            left_EAR = calculate_EAR(result.face_landmarks[0], LEFT_EYE_CORNERS, LEFT_EYE_LIDS)
            right_EAR = calculate_EAR(result.face_landmarks[0], RIGHT_EYE_CORNERS, RIGHT_EYE_LIDS)
            # Convert eye position to screen position
            if len(avg_calibration) == 4 and not flags.calibrating:
                both_closed = left_EAR < WINK_THRESHOLD and right_EAR < WINK_THRESHOLD
                smooth_x, smooth_y = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
                if not both_closed:  # Dont move during blinking
                    # use both eyes when both are open
                    smooth_x, smooth_y = calculate_smoothed_position(result.face_landmarks, prev_x, prev_y, w, h)
                elif left_EAR < WINK_THRESHOLD and right_EAR > WINK_THRESHOLD:
                    # use right eye if left is closed
                    smooth_x, smooth_y = calculate_right_smoothed_position(result.face_landmarks, prev_x, prev_y, w, h)
                elif left_EAR > WINK_THRESHOLD and right_EAR < WINK_THRESHOLD:
                    # use left eye if right is closed
                    smooth_x, smooth_y = calculate_right_smoothed_position(result.face_landmarks, prev_x, prev_y, w, h)

                if not both_closed:
                    prev_x, prev_y = smooth_x, smooth_y
                    io.move_mouse(smooth_x, smooth_y)


            # Winking check
            if left_EAR < WINK_THRESHOLD < right_EAR: # Left wink for left click
                flags.left_wink_frames += 1
                if flags.left_wink_frames == WINK_FRAMES_REQUIRED: # needs to happen over several frames to prevent accidental wink triggers
                    print("left wink")
                    io.left_click()
            elif left_EAR > WINK_THRESHOLD > right_EAR: # Right wink for right click
                flags.right_wink_frames += 1
                if flags.right_wink_frames == WINK_FRAMES_REQUIRED: # needs to happen over several frames to prevent accidental wink triggers
                    print("right wink")
                    io.right_click()
            else:
                flags.left_wink_frames = 0
                flags.right_wink_frames = 0

        # Show window with camera and tracking dots shown
        cv2.imshow("Face Landmarker", frame)

        #Keyboard inputs
        key = cv2.waitKey(1) & 0xFF
        if key == 27: # Quit
            flags.end_loop = True # to kill speech commands
            break
        elif key == ord("c") and flags.calibrating: # Add a start_calibrationcalibration point
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
                else:
                    print(f"And now please look to the {DIRECTIONS[len(avg_calibration)]}")
            else:
                print("Failed that calibration, please try again")

    # --- Cleanup ---
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()