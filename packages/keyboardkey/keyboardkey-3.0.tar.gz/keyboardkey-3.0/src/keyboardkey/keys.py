# keys.py
# Groups: functions, numbers, punctuations, cletters, sletters, controls, system, arrows

# Function keys (F-series only)
functions = [
    "f1", "f2", "f3", "f4", "f5", "f6",
    "f7", "f8", "f9", "f10", "f11", "f12"
]

# Numbers (top row + decimal)
numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "decimal"]

# Punctuations (symbols from your log)
punctuations = [
    "`", "-", "=", "/", "*", "+",
    "[", "]", "\\",  
    ";", "'", ",", ".",
    "~", "!", "@", "#", "$", "%", "^", "&",
    "(", ")", "_", "{", "}", "|",
    ":", "\"", "<", ">", "?"
]

# Capital letters
cletters = [
    "Q","W","E","R","T","Y","U","I","O","P",
    "A","S","D","F","G","H","J","K","L",
    "Z","X","C","V","B","N","M"
]

# Small letters
sletters = [
    "q","w","e","r","t","y","u","i","o","p",
    "a","s","d","f","g","h","j","k","l",
    "z","x","c","v","b","n","m"
]

# Control keys
controls = [
    "esc", "tab", "backspace", "enter", "caps lock",
    "shift", "right shift",
    "ctrl", "right ctrl",
    "left windows", "right windows",
    "alt", "alt gr",
    "space",
    "insert", "delete", "home", "end",
    "page up", "page down",
    "clear"
]

# System keys
system = [
    "menu", "num lock", "print screen", "scroll lock", "pause"
]

# Arrow keys
arrows = ["up", "down", "left", "right"]

# Combine all keys
everykey = functions + numbers + punctuations + cletters + sletters + controls + system + arrows
