import pyautogui

def move_mouse(x: float, y: float) -> None:
    pyautogui.moveTo(x, y)

def left_click() -> None:
    pyautogui.click(button='left')

def right_click() -> None:
    pyautogui.click(button='right')

def scroll(distance: float) -> None:
    pyautogui.scroll(distance)