import pyautogui
import string

# Write out the provided test
def type(text) -> None:
    pyautogui.write(text)

# Press the provided key
def type_char(char: string) -> None:
    pyautogui.press(char)

# Press and hold the provided key
def hold_char(char: string) -> None:
    pyautogui.keyDown(char)

# Unpress the provided key
def release_char(char: string) -> None:
    pyautogui.keyUp(char)
