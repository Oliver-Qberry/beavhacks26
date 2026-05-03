import speech_recognition as sr
# Using whisper
import os
import string
from rapidfuzz import fuzz
from flags import Flags

import controls.mouse as io
import controls.keyboard as keyboard_io


def debug_print(text):  # to make enabling/disabling all print functions easy
    print(text)
    pass


def fuzzy_equal(command, key) -> bool:
    acceptable_ratio = 70
    actual_ratio = fuzz.ratio(command, key)
    return actual_ratio > acceptable_ratio


def interpret_command(command, flags: Flags) -> None:
    if fuzzy_equal(command, "shutdown") or fuzzy_equal(command, "exit") or fuzzy_equal(command, "close"):
        flags.end_loop = True
    elif fuzzy_equal(command, "left") or fuzzy_equal(command, "click"):
        io.left_click()
    elif fuzzy_equal(command, "right"):
        io.right_click()
    elif fuzzy_equal(command, "scroll up"):
        io.scroll(10)
    elif fuzzy_equal(command, "scroll down"):
        io.scroll(-10)
    elif fuzzy_equal(command, "keyboard") or fuzzy_equal(command, "open keyboard"):
        flags.keyboard = True
    elif fuzzy_equal(command, "help"):
        print("'left' or 'click' to left click")
        print("'right' to right click")
        print("'scroll up' to scroll up")
        print("'scroll down' to scroll down")
        print("'keyboard' or 'open keyboard' to open keyboard/typing mode")
        print("'help' to print this info")
        print("'exit', 'shutdown', or 'close' to close the software")
    else:
        debug_print("Unknown command: \"" + command + "\"")


def interpret_keyboard(command, flags: Flags) -> None:
    check_command = command.strip().lower()
    check_command = "".join(filter(lambda x: x not in string.punctuation, check_command))
    if fuzzy_equal(check_command, "close keyboard"):
        flags.keyboard = False
    elif fuzzy_equal(check_command, "help"):
        print("'close keyboard' to close keyboard")
        print("'backspace' or 'delete' to delete the previous character")
        print("'move up/down/left/right' to move the text cursor")
        print("'undo' to undo")
        print("'space', 'escape', 'quote', 'backspace', 'period' to perform corresponding keyboard inputs")
        print("All other text is written as-is.")
    elif fuzzy_equal(check_command, "enter"):
        keyboard_io.type_char("enter")
    elif fuzzy_equal(check_command, "backspace big") or fuzzy_equal(check_command, "delete word"):
        keyboard_io.hold_char("ctrl")
        keyboard_io.hold_char("command")
        keyboard_io.type_char("backspace")
        keyboard_io.release_char("ctrl")
        keyboard_io.release_char("command")
        print("biggg backspace")
    elif fuzzy_equal(check_command, "backspace") or fuzzy_equal(check_command, "delete"):
        keyboard_io.type_char("backspace")
    elif fuzzy_equal(check_command, "space"):
        keyboard_io.type_char("space")
    elif fuzzy_equal(check_command, "move up"):
        keyboard_io.type_char("up")
    elif fuzzy_equal(check_command, "move down"):
        keyboard_io.type_char("down")
    elif fuzzy_equal(check_command, "move left"):
        keyboard_io.type_char("left")
    elif fuzzy_equal(check_command, "move right"):
        keyboard_io.type_char("right")
    elif fuzzy_equal(check_command, "escape") or fuzzy_equal(check_command, "cancel"):
        keyboard_io.type_char("escape")
    elif fuzzy_equal(check_command, "quote"):
        keyboard_io.type("\"")
    elif fuzzy_equal(check_command, "period"):
        keyboard_io.type(".")
    elif fuzzy_equal(check_command, "undo"):
        keyboard_io.hold_char("ctrl")
        keyboard_io.hold_char("command")
        keyboard_io.type_char("z")
        keyboard_io.release_char("ctrl")
        keyboard_io.release_char("command")
    elif fuzzy_equal(check_command, "hold shift"):
        keyboard_io.hold_char("shift")
    elif fuzzy_equal(check_command, "release shift"):
        keyboard_io.release_char("shift")
    else:
        keyboard_io.type(command.strip())