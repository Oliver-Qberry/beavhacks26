import speech_recognition as sr
# Using whisper
import os
import string
from rapidfuzz import fuzz
from flags import Flags

import controls.mouse as io
import controls.keyboard as io


def main() -> None:
    command = ""
    r = sr.Recognizer()
    r.energy_threshold = 1000 # Cull out some ambient noise
    flags = Flags()

    while not flags.end_loop:

        with sr.Microphone() as source:
            # r.adjust_for_ambient_noise(source, duration = 0.1)
            if flags.keyboard:
                # print("Say something to type")
                pass
            else:
                print("Give command")
            audio = r.listen(source)
        
        if not flags.keyboard:
            debug_print("Heard! interpreting...")
        try:
            # command = r.recognize_whisper(audio, language="english")
            # command = r.recognize_faster_whisper(audio, language="english")
            # command = r.recognize_sphinx(audio)
            command = r.recognize_google(audio)
            if not flags.keyboard:
                command = command.strip().lower()
                if command == "":
                    continue
                command = "".join(filter(lambda x: x not in string.punctuation, command))
                interpret_command(command, flags)
            else:
                interpret_keyboard(command, flags)
            
        except sr.UnknownValueError:
            print("Didn't get that. Could you say it again?")
        except sr.RequestError as e:
            print(f"Error: {e}")

    return

def debug_print(text): # to make enabling/disabling all print functions easy
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
        print(f"Keyboard is enabled: {flags.keyboard}")
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
        print("All other test is written as-is.")
    elif fuzzy_equal(check_command, "enter"):
        io.type_char("enter")
    elif fuzzy_equal(check_command, "backspace big") or fuzzy_equal(check_command, "delete word"):
        io.hold_char("ctrl")
        io.hold_char("command")
        io.type_char("backspace")
        io.release_char("ctrl")
        io.release_char("command")
        print("biggg backspace")
    elif fuzzy_equal(check_command, "backspace") or fuzzy_equal(check_command, "delete"):
        io.type_char("backspace")
    elif fuzzy_equal(check_command, "space"):
        io.type_char("space")
    elif fuzzy_equal(check_command, "move up"):
        io.type_char("up")
    elif fuzzy_equal(check_command, "move down"):
        io.type_char("down")
    elif fuzzy_equal(check_command, "move left"):
        io.type_char("left")
    elif fuzzy_equal(check_command, "move right"):
        io.type_char("right")
    elif fuzzy_equal(check_command, "escape") or fuzzy_equal(check_command, "cancel"):
        io.type_char("escape")
    elif fuzzy_equal(check_command, "quote"):
        io.type("\"")
    elif fuzzy_equal(check_command, "period"):
        io.type(".")
    elif fuzzy_equal(check_command, "undo"):
        io.hold_char("ctrl")
        io.hold_char("command")
        io.type_char("z")
        io.release_char("ctrl")
        io.release_char("command")
    elif fuzzy_equal(check_command, "hold shift"):
        io.hold_char("shift")
    elif fuzzy_equal(check_command, "release shift"):
        io.release_char("shift")
    else:
        io.type(command.strip())

if __name__ == '__main__':
    main()
