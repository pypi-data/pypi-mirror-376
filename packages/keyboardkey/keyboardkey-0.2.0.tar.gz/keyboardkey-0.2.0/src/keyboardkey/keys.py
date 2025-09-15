# keyboardkey v0.2.0
# Author: Aaron Geo Reji

# Letters
letters = [chr(i) for i in range(ord('a'), ord('z')+1)]

# Digits
digits = [str(i) for i in range(10)]

# Function keys
functions = [f"f{i}" for i in range(1, 13)]

# Navigation keys
navigation = [
    "up", "down", "left", "right",
    "home", "end", "pageup", "pagedown",
    "insert", "delete", "backspace", "tab",
    "enter", "escape", "esc", "space"
]

# System keys (includes modifiers)
system = [
    "shift", "ctrl", "alt", "win", "capslock", "numlock", "scrolllock",
    "printscreen", "pause", "break", "menu"
]

# Symbols / punctuation
symbols = [
    "`", "-", "=", "[", "]", "\\", ";", "'", ",", ".", "/",
    "~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", 
    "_", "+", "{", "}", "|", ":", "\"", "<", ">", "?"
]

# Numpad keys
numpad = [
    "num0", "num1", "num2", "num3", "num4",
    "num5", "num6", "num7", "num8", "num9",
    "num/", "num*", "num-", "num+", "num.", "numenter"
]

# Master list
everykey = (
    letters + digits + functions +
    navigation + system +
    symbols + numpad
)
