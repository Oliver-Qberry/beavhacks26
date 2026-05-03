import pyautogui

# Movie the mouse to the specified location on screen
def move_mouse(x: float, y: float) -> None:
    pyautogui.moveTo(x, y)

# Trigger a left mouse click
def left_click() -> None:
    pyautogui.click(button='left')

#Trigger a right mouse click
def right_click() -> None:
    pyautogui.click(button='right')

# Scroll based on the distance - it is sign sensitive
def scroll(distance: float) -> None:
    pyautogui.scroll(distance)