import keyboard

def show_key(event):
    print(f"event.name={event.name!r}, scan_code={event.scan_code}, vk={event.scan_code}")

keyboard.on_press(show_key)
print("Press some keys, ESC to quit")
keyboard.wait("esc")
