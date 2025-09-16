# keyboardkey Module

A Python module providing lists of all keyboard keys exactly as captured from a standard keyboard.

---

## Installation

Install the module from PyPI using pip:

```bash
pip install keyboardkey

---

## Usage

```python
from keys import functions, numbers, punctuations, cletters, sletters, controls, system, arrows, everykey

# Print all function keys (F1–F12)
print("Function keys:", functions)

# Print all numbers including decimal
print("Numbers:", numbers)

# Print all punctuation symbols
print("Punctuations:", punctuations)

# Print all capital letters
print("Capital letters:", cletters)

# Print all small letters
print("Small letters:", sletters)

# Print all control keys
print("Control keys:", controls)

# Print all system keys
print("System keys:", system)

# Print all arrow keys
print("Arrow keys:", arrows)

# Print all keys combined
print("Every key:", everykey)
