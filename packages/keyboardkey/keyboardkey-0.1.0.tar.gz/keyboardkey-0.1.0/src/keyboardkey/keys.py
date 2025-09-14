# keys.py

# Letters
letters = [chr(i) for i in range(ord('a'), ord('z') + 1)]

# Digits
digits = [str(i) for i in range(10)]

# Function keys
function_keys = [f"f{i}" for i in range(1, 13)]

# Arrow keys
arrow_keys = ["up", "down", "left", "right"]

# Control keys
control_keys = ["enter", "esc", "tab", "backspace", "space", "shift", "ctrl", "alt", "capslock"]

# Special characters
specials = list("!@#$%^&*()_-+={}[]|:;\"'<>,.?/`~")

# All keys together
every_key = letters + digits + function_keys + arrow_keys + control_keys + specials
