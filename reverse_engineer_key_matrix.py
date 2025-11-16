import keyboard
import re

ZMK_MATRIX = """
                &kp A       &kp B      &kp C      &kp D     &kp E     &kp F       &kp G        &kp H     &kp I    &kp J      // ROW 0 
                &kp K       &kp L      &kp M      &kp N     &kp O     &kp P       &kp Q        &kp R     &kp S    &kp T      // ROW 1 
                &kp U       &kp V      &kp W      &kp X     &kp Y     &kp Z       &kp N1       &kp N2    &kp N3   &kp N4     // ROW 2 
                &kp N5      &kp N6     &kp N7     &kp N8    &kp N9    &kp N0      &kp MINUS    &kp EQUAL &kp LBKT &kp RBKT   // ROW 3 
                &kp BSLH    &kp GRAVE  &kp SEMI   &kp SQT   &kp COMMA &kp DOT     &kp FSLH     &kp TAB   &kp ENTER &kp SPC    // ROW 4 
                &kp BSPC    &kp ESC    &kp F1     &kp F2    &kp F3    &kp F4      &kp F5       &kp F6    &kp F7   &kp F8     // ROW 5 
                &kp F9      &kp F10    &kp F11    &kp F12   &kp F13   &kp LSHFT   &kp LCTRL    &kp LALT  &kp RSHFT &kp RCTRL // ROW 6 
                &kp INS     &kp DEL    &kp HOME   &kp END   &kp PG_UP &kp PG_DN   &kp UP       &kp DOWN  &kp LEFT &kp RIGHT  // ROW 7
"""

ZMK_MATRIX = """
                  &kp A       &kp B      &kp C      &kp D     &kp E     &kp F       &kp G        &kp H     &kp I     &kp J     &kp KP_N1    &kp KP_N2  // ROW 0 
                  &kp K       &kp L      &kp M      &kp N     &kp O     &kp P       &kp Q        &kp R     &kp S     &kp T     &kp KP_N3    &kp KP_N4  // ROW 1 
                  &kp U       &kp V      &kp W      &kp X     &kp Y     &kp Z       &kp N1       &kp N2    &kp N3    &kp N4    &kp KP_N5    &kp KP_N6  // ROW 2 
                  &kp N5      &kp N6     &kp N7     &kp N8    &kp N9    &kp N0      &kp MINUS    &kp EQUAL &kp LBKT  &kp RBKT  &kp KP_N7    &kp KP_N8  // ROW 3 
                  &kp BSLH    &kp GRAVE  &kp SEMI   &kp SQT   &kp COMMA &kp DOT     &kp FSLH     &kp TAB   &kp ENTER &kp SPC   &kp KP_N9    &kp KP_DOT // ROW 4 
                  &kp BSPC    &kp ESC    &kp F1     &kp F2    &kp F3    &kp F4      &kp F5       &kp F6    &kp F7    &kp F8    &kp KP_PLUS  &kp KP_MINUS // ROW 5 
                  &kp F9      &kp F10    &kp F11    &kp F12   &kp F13   &kp LSHFT   &kp LCTRL    &kp LALT  &kp RSHFT &kp RCTRL &kp KP_SLASH &kp KP_ASTERISK // ROW 6 
                  &kp INS     &kp DEL    &kp HOME   &kp END   &kp PG_UP &kp PG_DN   &kp UP       &kp DOWN  &kp LEFT  &kp RIGHT &kp KP_ENTER &kp KP_EQUAL // ROW 7
"""

print("Change to QWERTY (US) on windows!!")

# 1. Parse the ZMK table into a matrix (row, col)
matrix = []
for line in ZMK_MATRIX.strip().splitlines():
    # extract all "&kp SOMETHING" tokens
    row = re.findall(r"&\w+\s+\w+", line)
    matrix.append(row)

# 2. Flatten into lookup {zmk_code: (row, col)}
zmk_lookup = {}
for r, row in enumerate(matrix):
    for c, code in enumerate(row):
        zmk_lookup[code.strip()] = (r, c)

# 3. Map keyboard names → ZMK codes
# (extend as needed)
keyboard_to_zmk = {
    # Letters
    "a": "&kp A", "b": "&kp B", "c": "&kp C", "d": "&kp D", "e": "&kp E",
    "f": "&kp F", "g": "&kp G", "h": "&kp H", "i": "&kp I", "j": "&kp J",
    "k": "&kp K", "l": "&kp L", "m": "&kp M", "n": "&kp N", "o": "&kp O",
    "p": "&kp P", "q": "&kp Q", "r": "&kp R", "s": "&kp S", "t": "&kp T",
    "u": "&kp U", "v": "&kp V", "w": "&kp W", "x": "&kp X", "y": "&kp Y",
    "z": "&kp Z",

    # Numbers
    "1": "&kp N1", "2": "&kp N2", "3": "&kp N3", "4": "&kp N4", "5": "&kp N5",
    "6": "&kp N6", "7": "&kp N7", "8": "&kp N8", "9": "&kp N9", "0": "&kp N0",

    # Punctuation
    "-": "&kp MINUS", "=": "&kp EQUAL", "[": "&kp LBKT", "]": "&kp RBKT",
    "\\": "&kp BSLH", "`": "&kp GRAVE", ";": "&kp SEMI", "'": "&kp SQT",
    ",": "&kp COMMA", ".": "&kp DOT", "/": "&kp FSLH",

    # Standard keys
    "tab": "&kp TAB", "enter": "&kp ENTER", "space": "&kp SPC", "backspace": "&kp BSPC",
    "esc": "&kp ESC",

    # Function keys
    "f1": "&kp F1", "f2": "&kp F2", "f3": "&kp F3", "f4": "&kp F4",
    "f5": "&kp F5", "f6": "&kp F6", "f7": "&kp F7", "f8": "&kp F8",
    "f9": "&kp F9", "f10": "&kp F10", "f11": "&kp F11", "f12": "&kp F12",
    "f13": "&kp F13", "f14": "&kp F14", "f15": "&kp F15", "f16": "&kp F16",
    "f17": "&kp F17", "f18": "&kp F18", "f19": "&kp F19", "f20": "&kp F20",
    "f21": "&kp F21", "f22": "&kp F22", "f23": "&kp F23", "f24": "&kp F24",

    # Modifiers
    "left shift": "&kp LSHFT", "right shift": "&kp RSHFT", "shift": "&kp LSHFT",
    "left ctrl": "&kp LCTRL", "right ctrl": "&kp RCTRL", "ctrl": "&kp LCTRL",
    "left alt": "&kp LALT", "right alt": "&kp LALT", "alt": "&kp LALT",

    # Navigation / special
    "insert": "&kp INS", "delete": "&kp DEL", "home": "&kp HOME", "end": "&kp END",
    "page up": "&kp PG_UP", "pgup": "&kp PG_UP",
    "page down": "&kp PG_DN", "pgdn": "&kp PG_DN",
    "up": "&kp UP", "down": "&kp DOWN", "left": "&kp LEFT", "right": "&kp RIGHT",
    "menu": "&kp MENU", "break": "&kp BREAK",

    # Numpad keys
    "num 1": "&kp KP_N1", "num 2": "&kp KP_N2", "num 3": "&kp KP_N3", "num 4": "&kp KP_N4",
    "num 5": "&kp KP_N5", "num 6": "&kp KP_N6", "num 7": "&kp KP_N7", "num 8": "&kp KP_N8",
    "num 9": "&kp KP_N9", "num 0": "&kp KP_N0", "num .": "&kp KP_DOT",
    "num +": "&kp KP_PLUS", "num -": "&kp KP_MINUS", "num *": "&kp KP_ASTERISK",
    "num /": "&kp KP_SLASH", "num enter": "&kp KP_ENTER", "num =": "&kp KP_EQUAL",
}


# 4. Event handler
def on_key(event):
    key = event.name.lower()
    if key in keyboard_to_zmk:
        zmk_code = keyboard_to_zmk[key]
        if zmk_code in zmk_lookup:
            row, col = zmk_lookup[zmk_code]
            #print(f"{zmk_code} -> RC({row}, {col})")
            print(f"RC({row}, {col})")
        else:
            print(f"{zmk_code} not in matrix")
    else:
        print(f"Unmapped key: {event.name}")

keyboard.on_press(on_key)
print("Listening for key presses... Press ESC twice to quit.")
keyboard.wait("esc")
