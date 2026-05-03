import pyautogui
import string

def type(text) -> None:
    pyautogui.write(text)

def type_char(char: string) -> None:
    pyautogui.press(char)

def hold_char(char: string) -> None:
    pyautogui.keyDown(char)

def release_char(char: string) -> None:
    pyautogui.keyUp(char)
