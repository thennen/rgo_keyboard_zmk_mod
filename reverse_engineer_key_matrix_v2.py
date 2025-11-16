# zmk_matrix_watcher.py
import re
import keyboard
from collections import defaultdict

ZMK_MATRIX = """
                  &kp A       &kp B      &kp C      &kp D     &kp E     &kp F       &kp G        &kp H     &kp I     &kp J     &kp F13    &kp F14
                  &kp K       &kp L      &kp M      &kp N     &kp O     &kp P       &kp Q        &kp R     &kp S     &kp T     &kp F15    &kp F16
                  &kp U       &kp V      &kp W      &kp X     &kp Y     &kp Z       &kp N1       &kp N2    &kp N3    &kp N4    &kp F17    &kp F18
                  &kp N5      &kp N6     &kp N7     &kp N8    &kp N9    &kp N0      &kp MINUS    &kp EQUAL &kp LBKT  &kp RBKT  &kp F19    &kp F20
                  &kp GRAVE   &kp SQT    &kp SEMI   &kp COMMA &kp DOT   &kp FSLH    &kp BSLH     &kp TAB   &kp ENTER &kp SPC   &kp F21    &kp F22
                  &kp BSPC    &kp ESC    &kp F1     &kp F2    &kp F3    &kp F4      &kp F5       &kp F6    &kp F7    &kp F8    &kp F23    &kp F24
                  &kp F9      &kp F10    &kp F11    &kp F12   &kp PSCRN &kp LSHFT   &kp LCTRL    &kp LALT  &kp RSHFT &kp RCTRL &kp PAUSE_BREAK &kp SLCK
                  &bootloader &kp DEL    &kp HOME   &kp END   &kp PG_UP &kp PG_DN   &kp UP       &kp DOWN  &kp LEFT  &kp RIGHT &kp CLEAR  &kp INS
"""

# ---------- parse matrix ----------
token_re = re.compile(r"(&[A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)?)")
rows = []
for line in ZMK_MATRIX.strip().splitlines():
    tokens = token_re.findall(line)
    # normalize whitespace in token, e.g. "&kp   A" -> "&kp A"
    row = [' '.join(t.split()) for t in tokens]
    if row:
        rows.append(row)

# sanity check
expected_cols = 12
if any(len(r) != expected_cols for r in rows):
    print("Warning: parsed matrix rows have varying lengths. Parsed row lengths:", [len(r) for r in rows])

# canonicalizer for ZMK tokens so comparisons match (we store canonical strings)
def canonical_zmk(tok: str) -> str:
    tok = ' '.join(tok.split())
    if tok.lower().startswith('&kp '):
        # &kp A  -> &kp A (capitalise code part)
        parts = tok.split()
        if len(parts) >= 2:
            return '&kp ' + parts[1].upper()
    # other things like &bootloader, &kp PAUSE_BREAK, &kp PSCRN keep as-lower/upper consistent:
    # keep leading & lower-case, but code part as-is (use upper for known words)
    return tok.upper() if tok.startswith('&KP') else tok.lower()

matrix = [[canonical_zmk(cell) for cell in row] for row in rows]
zmk_lookup = { cell: (r, c) for r, row in enumerate(matrix) for c, cell in enumerate(row) }

# ---------- keyboard name -> ZMK mapping (name strings are what keyboard module reports) ----------
# We intentionally DO NOT map numpad names like "num 1" -> any &kp (you said take keypad stuff out).
keyboard_to_zmk = {
    # letters
    **{ch: f"&kp {ch.upper()}" for ch in "abcdefghijklmnopqrstuvwxyz"},

    # top-row numbers (N1..N0)
    "1": "&kp N1", "2": "&kp N2", "3": "&kp N3", "4": "&kp N4", "5": "&kp N5",
    "6": "&kp N6", "7": "&kp N7", "8": "&kp N8", "9": "&kp N9", "0": "&kp N0",

    # punctuation (non-shifted)
    "-": "&kp MINUS", "=": "&kp EQUAL", "[": "&kp LBKT", "]": "&kp RBKT",
    "`": "&kp GRAVE", "'": "&kp SQT", ";": "&kp SEMI", ",": "&kp COMMA",
    ".": "&kp DOT", "/": "&kp FSLH", "\\": "&kp BSLH",

    # control / navigation
    "enter": "&kp ENTER", "return": "&kp ENTER", "tab": "&kp TAB", "space": "&kp SPC",
    "backspace": "&kp BSPC", "esc": "&kp ESC", "escape": "&kp ESC",
    "delete": "&kp DEL", "del": "&kp DEL", "home": "&kp HOME", "end": "&kp END",
    "page up": "&kp PG_UP", "pgup": "&kp PG_UP", "page down": "&kp PG_DN", "pgdn": "&kp PG_DN",
    "up": "&kp UP", "down": "&kp DOWN", "left": "&kp LEFT", "right": "&kp RIGHT",

    # function keys (F1..F24) — include F13..F24 so a keyboard that reports them still works
    **{f"f{i}": f"&kp F{i}" for i in range(1, 25)},

    # modifiers
    "shift": "&kp LSHFT", "left shift": "&kp LSHFT", "right shift": "&kp RSHFT",
    "ctrl": "&kp LCTRL", "left ctrl": "&kp LCTRL", "right ctrl": "&kp RCTRL",
    "alt": "&kp LALT", "left alt": "&kp LALT", "right alt": "&kp LALT",

    # a few special keys we added in the matrix
    "print screen": "&kp PSCRN", "printscreen": "&kp PSCRN", "pscrn": "&kp PSCRN",
    "pause": "&kp PAUSE_BREAK", "pause break": "&kp PAUSE_BREAK", "scroll lock": "&kp SLCK", "scrolllock": "&kp SLCK",
    "clear": "&kp CLEAR", "sysrq": "&kp SYSREQ", "sysreq": "&kp SYSREQ",
}

# canonicalize values in keyboard_to_zmk
keyboard_to_zmk = {k: canonical_zmk(v) for k, v in keyboard_to_zmk.items()}

# ---------- optional per-keyboard scan-code overrides ----------
# Fill this map if you want to map a particular scan_code (physical key) to a ZMK code.
# Example: scan_code_map[28] = '&kp ENTER'   # (your keyboard might send scan_code 28 for Enter)
scan_code_map = {
    # example (empty by default). Add entries if your keyboard reports weird scan_codes:
    # 28: '&kp ENTER',
    # 74: '&kp LEFT'   # etc.
}
# canonicalize scan_code_map values
scan_code_map = {k: canonical_zmk(v) for k, v in scan_code_map.items()}

# ---------- event handling ----------
def on_event(e):
    # only act on key down to avoid duplicates
    try:
        if getattr(e, "event_type", None) and e.event_type != "down":
            return
    except Exception:
        pass

    name = (e.name or "").lower()
    sc = getattr(e, "scan_code", None)

    # try scan-code override first (recommended if your keyboard layout/registry makes names unreliable)
    if sc in scan_code_map:
        zmk = scan_code_map[sc]
        if zmk in zmk_lookup:
            r, c = zmk_lookup[zmk]
            print(f"{zmk} -> RC({r}, {c})")
            return
        else:
            print(f"{zmk} (from scan_code {sc}) not present in the parsed matrix.")
            return

    # then try name-based mapping
    if name in keyboard_to_zmk:
        zmk = keyboard_to_zmk[name]
        if zmk in zmk_lookup:
            r, c = zmk_lookup[zmk]
            print(f"{zmk} -> RC({r}, {c})")
            return
        else:
            print(f"{zmk} is a known ZMK code but not located in the present matrix.")
            return

    # unmapped: help the user add a scan-code override
    print(f"Unmapped key: name={name!r}, scan_code={sc}.")
    print(f"  To map this scan code add an entry like: scan_code_map[{sc}] = '&kp YOUR_KEY' and canonicalize the value.")

# install hook
keyboard.hook(on_event)
print("Listening for key presses (press ESC to stop).")
keyboard.wait("esc")
