import speech_recognition as sr
# Using whisper
import os
import string
from rapidfuzz import fuzz

class Flags():
    end_loop = False
    keyboard = False
    
    def __init__(self):
        print("constructed")

def main() -> None:
    command = ""
    r = sr.Recognizer()
    r.energy_threshold = 1000 # Cull out some ambient noise
    
    flags = Flags()

    while not flags.end_loop:

        with sr.Microphone() as source:
            if flags.keyboard:
                # print("Say something to type")
                pass
            else:
                print("Give command")
            audio = r.listen(source)
        
        if not flags.keyboard:
            debug_print("Heard! interpreting...")
        try:
            command = r.recognize_whisper(audio, language="english")
            if not flags.keyboard:
                command = command.strip().lower()
                if command == "":
                    debug_print("nothing, continuing")
                    continue
                command = "".join(filter(lambda x: x not in string.punctuation, command))
                interpret_command(command, flags)
            else:
                check_command = command.strip().lower()
                check_command = "".join(filter(lambda x: x not in string.punctuation, check_command))
                if fuzzy_equal(check_command, "close keyboard"):
                    print("Closing keyboard.")
                    flags.keyboard = False
                    continue
                print(command)
            
        except sr.UnknownValueError:
            print("Whisper could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Whisper; {e}")

    return

def debug_print(text): # to make enabling/disabling all print functions easy
    print(text)
    pass
    
def fuzzy_equal(command, key) -> bool:
    acceptable_ratio = 70
    actual_ratio = fuzz.ratio(command, key)
    return actual_ratio > acceptable_ratio

def interpret_command(command, flags: Flags) -> None:
    if fuzzy_equal(command, "exit"):
        debug_print("Exiting!")
        flags.end_loop = True
    elif fuzzy_equal(command, "left") or fuzzy_equal(command, "click"):
        debug_print("Left click")
    elif fuzzy_equal(command, "right"):
        debug_print("Right click")
    elif fuzzy_equal(command, "scroll up"):
        debug_print("Scrolling up")
    elif fuzzy_equal(command, "scroll down"):
        debug_print("Scrolling down")
    elif fuzzy_equal(command, "keyboard") || fuzzy_equal(command, "open keyboard"):
        debug_print("Opening keyboard")
        flags.keyboard = True
    elif fuzzy_equal(command, "help"):
        print("'left' or 'click' to left click")
        print("'right' to right click")
        print("'scroll up' to scroll up")
        print("'scroll down' to scroll down")
        print("'keyboard' or 'open keyboard' to open keyboard/typing mode")
        print("'close keyboard' while keyboard is open to close it")
        print("'help' to print this info")
        print("'exit' to close the software")
    else:
        debug_print("Unknown command: \"" + command + "\"")

if __name__ == '__main__':
    main()
