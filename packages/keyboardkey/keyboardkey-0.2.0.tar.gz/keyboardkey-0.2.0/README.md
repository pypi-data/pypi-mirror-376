# keyboardkey v0.2.0

A Python module providing lists of real keyboard keys (letters, digits, function keys, arrows, symbols, system keys, and numpad).

---

## Installation
```bash
pip install keyboardkey

---

### Usage

```python
from keyboardkey import everykey, letters, digits, functions, arrows, modifiers, special_keys

# Print all keys
print("All keys:")
print(everykey)

# Print letters
print("\nLetters:")
print(letters)

# Print digits
print("\nDigits:")
print(digits)

# Print function keys F1–F12
print("\nFunction keys:")
print(functions)

# Print arrow keys
print("\nArrow keys:")
print(arrows)

# Print modifier keys (Ctrl, Shift, Alt, etc.)
print("\nModifier keys:")
print(modifiers)

# Print other special keys
print("\nSpecial keys:")
print(special_keys)
