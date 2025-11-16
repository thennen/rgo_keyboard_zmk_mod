#!/usr/bin/env python3
"""
zmk_key_logger_windows.py

Captures global keyboard events on Windows and prints a textual ZMK keycode
name for every press/release.

Requires: pip install keyboard
Run as Administrator (needed by the keyboard module for global hooks).
"""
import keyboard
import time

# ---------------------------
# Mapping from keyboard library names/scan codes to ZMK keycode strings.
# This mapping covers letters, numbers, function keys, modifiers, keypad,
# editing/navigation, media/consumer keys, application keys, and common others.
# Extend this dict if your hardware emits other names/scan codes.
# ---------------------------

# Helper to construct number names N1..N0 (ZMK uses N1..N0 for top-row digits)
def _num_name(n):
    return "N" + str(n % 10)

MAP = {
    # Letters
    **{chr(c): chr(c).upper() for c in range(ord('a'), ord('z')+1)},  # 'a'->'A', ...

    # Numbers/top row (keyboard module uses '1','2',...,'0' as names)
    '1': 'N1', '2': 'N2', '3': 'N3', '4': 'N4', '5': 'N5',
    '6': 'N6', '7': 'N7', '8': 'N8', '9': 'N9', '0': 'N0',

    # Function keys
    'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4', 'f5': 'F5',
    'f6': 'F6', 'f7': 'F7', 'f8': 'F8', 'f9': 'F9', 'f10': 'F10',
    'f11': 'F11', 'f12': 'F12', 'f13': 'F13', 'f14': 'F14', 'f15': 'F15',
    'f16': 'F16', 'f17': 'F17', 'f18': 'F18', 'f19': 'F19', 'f20': 'F20',

    # Modifiers
    'left shift': 'LEFT_SHIFT', 'right shift': 'RIGHT_SHIFT',
    'left ctrl': 'LEFT_CTRL', 'right ctrl': 'RIGHT_CTRL',
    'left alt': 'LEFT_ALT', 'right alt': 'RIGHT_ALT',
    'left windows': 'LEFT_GUI', 'right windows': 'RIGHT_GUI',  # Windows key reported as 'left windows' etc.

    # Common controls
    'enter': 'ENTER', 'space': 'SPACE', 'tab': 'TAB', 'backspace': 'BACKSPACE',
    'esc': 'ESCAPE', 'escape': 'ESCAPE',
    'caps lock': 'CAPS_LOCK', 'print screen': 'PRINT_SCREEN', 'scroll lock': 'SCROLL_LOCK',
    'pause': 'PAUSE', 'insert': 'INSERT', 'delete': 'DELETE',
    'home': 'HOME', 'end': 'END', 'page up': 'PAGE_UP', 'page down': 'PAGE_DOWN',
    'up': 'UP', 'down': 'DOWN', 'left': 'LEFT', 'right': 'RIGHT',

    # Punctuation and symbols (common names used by keyboard package)
    'minus': 'MINUS', 'equals': 'EQUALS', 'left bracket': 'LEFT_BRACKET',
    'right bracket': 'RIGHT_BRACKET', 'backslash': 'BACKSLASH',
    'semicolon': 'SEMICOLON', 'quote': 'APOSTROPHE', 'comma': 'COMMA',
    'dot': 'DOT', 'period': 'DOT', 'slash': 'SLASH',
    'grave': 'GRAVE',  # backtick `
    
    # Numpad (names vary; keyboard library uses 'num ...' or 'numpad ...' on some systems)
    'num lock': 'NUM_LOCK',
    'numpad 0': 'KP_0', 'numpad 1': 'KP_1', 'numpad 2': 'KP_2', 'numpad 3': 'KP_3',
    'numpad 4': 'KP_4', 'numpad 5': 'KP_5', 'numpad 6': 'KP_6', 'numpad 7': 'KP_7',
    'numpad 8': 'KP_8', 'numpad 9': 'KP_9',
    'numpad divide': 'KP_SLASH', 'numpad multiply': 'KP_ASTERISK',
    'numpad subtract': 'KP_MINUS', 'numpad add': 'KP_PLUS',
    'numpad decimal': 'KP_DOT', 'numpad enter': 'KP_ENTER',

    # Editing/navigation (ZMK names chosen to match common ZMK naming)
    'page up': 'PAGE_UP', 'page down': 'PAGE_DOWN', 'home': 'HOME', 'end': 'END',
    'print screen': 'PRINT_SCREEN', 'application': 'APP',  # Application/Menu key

    # Media / Consumer controls (names may differ by OS/driver)
    'play/pause media': 'MEDIA_PLAY_PAUSE', 'play/pause': 'MEDIA_PLAY_PAUSE', 'play': 'MEDIA_PLAY',
    'pause media': 'MEDIA_PAUSE', 'stop media': 'MEDIA_STOP',
    'next track': 'MEDIA_NEXT_TRACK', 'previous track': 'MEDIA_PREV_TRACK',
    'volume up': 'MEDIA_VOL_UP', 'volume down': 'MEDIA_VOL_DOWN', 'mute': 'MEDIA_MUTE',

    # Browser/application shortcuts (may be reported differently)
    'browser back': 'C_BROWSER_BACK', 'browser forward': 'C_BROWSER_FORWARD',
    'browser refresh': 'C_BROWSER_REFRESH', 'browser stop': 'C_BROWSER_STOP',
    'browser search': 'C_BROWSER_SEARCH', 'browser favorites': 'C_BROWSER_FAVORITES',
    'browser home': 'C_BROWSER_HOME',

    # Application launch / special
    'launch mail': 'C_MAIL', 'launch media player': 'C_MEDIA', 'calculator': 'C_CALCULATOR',

    # Input assist, power & lock (ZMK provides codes for many of these)
    'sleep': 'SYSTEM_SLEEP', 'power': 'SYSTEM_POWER', 'wake': 'SYSTEM_WAKE',

    # Some alternate names captured on Windows
    'left windows': 'LEFT_GUI', 'right windows': 'RIGHT_GUI',
    'menu': 'APP',
}

# Add explicit numeric synonyms to MAP (just in case)
MAP.update({
    'dot': 'DOT', '.': 'DOT',
    'comma': 'COMMA', ',': 'COMMA',
    '-': 'MINUS', '=': 'EQUALS', '/': 'SLASH', '\\': 'BACKSLASH',
    '`': 'GRAVE', "'": 'APOSTROPHE', ';': 'SEMICOLON', '[': 'LEFT_BRACKET', ']': 'RIGHT_BRACKET',
})

# ---------------------------
# Helper functions
# ---------------------------
def zmk_for_event(e):
    """
    Given a keyboard.KeyboardEvent, return a ZMK string if known, otherwise None.
    """
    name = e.name  # e.g. 'a', 'space', 'left shift', 'f1', etc.
    if name is None:
        return None
    # keyboard module sometimes reports uppercase letters; normalize to lowercase for mapping keys like 'a'
    ln = name.lower()

    # direct mapping
    if ln in MAP:
        return MAP[ln]

    # If the name is a single printable char and letter/digit, handle letter/digit fallback
    if len(ln) == 1 and ln.isalpha():
        return ln.upper()
    if len(ln) == 1 and ln.isdigit():
        return "N" + ln if ln != '0' else "N0"

    # Try common prefixes e.g. 'numpad 1' or 'numpad1'
    if ln.startswith('numpad'):
        return MAP.get(ln, None)

    # Fallback to a cleaned name (uppercase, spaces to underscores) to let user map manually
    cleaned = ln.replace(' ', '_').upper()
    return cleaned  # this may already match many ZMK names like MEDIA_PLAY_PAUSE etc.

# ---------------------------
# Event handlers
# ---------------------------
def on_event(e):
    # e.event_type = 'down' or 'up'
    # e.name = normalized name (may be None)
    # e.scan_code = integer scan code
    zmk = zmk_for_event(e)
    direction = "PRESS" if e.event_type == 'down' else "RELEASE"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if zmk:
        print(f"{timestamp} {direction}: {zmk}")
    else:
        print(f"{timestamp} {direction}: <unknown: name={e.name!r} scan={e.scan_code}>")

# ---------------------------
# Main
# ---------------------------
def main():
    print("ZMK key logger (Windows) — listening for keys. Press ESC to quit.")
    # Hook all keyboard events
    keyboard.hook(on_event)
    # Keep running until Escape is pressed (we still print Escape events)
    keyboard.wait('esc')
    print("Exiting.")

if __name__ == "__main__":
    main()
