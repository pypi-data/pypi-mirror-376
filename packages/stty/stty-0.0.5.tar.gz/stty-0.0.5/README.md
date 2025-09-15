# stty.py

A Python library for manipulating terminal settings in the style of POSIX `stty(1)`.

---

## Overview

`stty` provides a high-level, Pythonic interface to terminal I/O settings, including control characters, baud rates, and window size, using the `termios` and related modules. It allows you to get, set, save, and restore terminal attributes, and to apply them to file descriptors or pseudo-terminals.

---

## Features

- Read and modify terminal attributes (iflag, oflag, cflag, lflag, control characters, speeds, window size)
- Save and load settings to/from JSON files
- Apply settings to file descriptors or pseudo-terminals
- Symbolic and string-based access to all settings
- Emulates many `stty(1)` features and modes (e.g., raw, evenp, oddp, nl, ek)
- Cross-platform support (where `termios` is available)

---

## Requirements and Installation

**Python 3.13 or above** is required. To install this package, run:

```bash
pip install stty
```

Alternatively, since this library does not have any dependencies outside of the Python standard library, simply place `stty.py` in your project.

---

## Examples

### 1. Reading and Printing Terminal Settings

```python
from stty import Stty

# Open terminal and get current settings from stdin (fd=0)
tty = Stty(fd=0)
print(tty)  # Print all settings in a compact form
```

---

### 2. Setting Individual Attributes

```python
from stty import Stty

tty = Stty(fd=0)

# Turn off echo
tty.echo = False

# Set erase character to Ctrl-H
tty.erase = "^H"

# Set input baud rate to 9600
tty.ispeed = 9600

# Set number of rows in the terminal window (if supported)
tty.rows = 40
```

---

### 3. Setting Multiple Attributes at Once

```python
from stty import Stty

tty = Stty(fd=0)

# Set several attributes in one call
tty.set(
    echo=False,
    icanon=False,
    erase="^H",
    ispeed=19200,
    ospeed=19200,
    rows=30,
    cols=100
)
```

---

### 4. Saving and Loading Settings

```python
from stty import Stty

tty = Stty(fd=0)

# Save current settings to a file
tty.save("my_tty_settings.json")

# Later, restore settings from the file
tty2 = Stty(path="my_tty_settings.json")
tty2.tofd(0)  # Apply to stdin
```

---

### 5. Using Raw Mode

```python
from stty import Stty

tty = Stty(fd=0)
tty.raw()         # Set raw mode
tty.tofd(0)       # Apply to stdin
```

---

### 6. Working with Pseudo-terminals

```python
from stty import Stty

tty = Stty(fd=0)
m, s, sname = tty.openpty()  # Open a new pty pair and apply settings to slave
print(f"Master fd: {m}, Slave fd: {s}, Slave name: {sname}")
```

---

### 7. Setting Control Characters

```python
from stty import Stty

tty = Stty(fd=0)

# Set interrupt character to Ctrl-C
tty.intr = "^C"

# Set end-of-file character to Ctrl-D
tty.eof = "^D"

# Set suspend character to DEL
tty.susp = "^?"
```

---

### 8. Querying Settings as a Dictionary

```python
from stty import Stty

tty = Stty(fd=0)
settings = tty.get()
print(settings["echo"])   # True or False
print(settings["erase"])  # e.g., '^H'
```

---

### 9. Using Symbolic Constants

```python
from stty import Stty, cs8, tab0

tty = Stty(fd=0)

# Set character size to 8 bits using symbolic constant
tty.csize = cs8

# Set tab delay to tab0
tty.tabdly = tab0
```

---

### 10. Fork new process with pseudo-terminal

```python
x = stty.Stty(0)
x.intr = "^p"
pid, m, sname  = x.forkpty()

if pid == 0: # Child process
    with open("out", "w") as f:
        f.write(str(stty.Stty(0)))
else: # Parent process
    print(sname)
    print("")
    s = os.open(sname, os.O_RDWR)
    print("Parent:", stty.Stty(s))
    os.close(s)
```

---

### 11. Check equality of (all termios and winsize attributes of) 2 Stty objects

```python
x = stty.Stty(0)
y = stty.Stty(0)

if x.get() == y.get():
    print("equal")
else:
    print("not equal")
```

---

### 12. Check equality of (some termios and winsize attributes of) 2 Stty objects

```python
x = stty.Stty(0)

if x.eq(echo=True, eof="^D")
    print("echo is True and eof is ^D")
else:
    print("echo is False or eof is not ^D")
```

---

## API Reference

### Classes

#### `Stty`

Manipulate terminal settings in the style of `stty(1)`.

**Constructor:**
```python
Stty(fd: int = None, path: str = None, **opts)
```
- `fd`: File descriptor to read settings from.
- `path`: Path to JSON file to load settings from.
- `**opts`: Any supported terminal attribute as a keyword argument.

**Methods:**

- `get() -> dict`
  Return dictionary of termios and winsize attributes available on the system mapped to their respective values.

- `set(**opts)`
  Set multiple attributes as named arguments.

- `eq(**opts)`
  Return True if all attributes, which are specified as named arguments, have values equal to those of the corresponding named arguments; return False otherwise.

- `save(path: str = None)`
  Return deep copy of self or save JSON. This mimics "stty -g".

- `load(path: str)`
  Load termios and winsize from JSON file.

- `fromfd(fd: int)`
  Get settings from terminal.

- `tofd(fd: int, when=TCSANOW, apply_termios=True, apply_winsize=True)`
  Apply settings to terminal.

- `evenp(plus=True)`
  Set/unset evenp combination mode.

- `oddp(plus=True)`
  Set/unset oddp combination mode.

- `raw()`
  Set raw combination mode.

- `nl(plus=True)`
  Set/unset nl combination mode.

- `ek()`
  Set ek combination mode.

- `openpty(apply_termios=True, apply_winsize=True)`
  Open a new pty pair and apply settings to slave end.

- `forkpty(apply_termios=True, apply_winsize=True)`
  Call os.forkpty() and apply settings to slave end.

**Attribute Access:**

- All terminal attributes (e.g., `echo`, `icanon`, `erase`, `ispeed`, `rows`, etc.) are accessible as properties.
- Setting an attribute updates the internal state and validates the value.

---

### Constants

- `TCSANOW`, `TCSADRAIN`, `TCSAFLUSH`: the values accepted by the `when` named argument of `Stty.tofd()`. Compare with `termios.tcsetattr()`.
- Symbolic constants for masks and values (e.g., `cs8`, `tab0`, etc.) are available as module attributes.

---

### Data

- `settings`: A dictionary describing all available Stty attributes and their possible values on the current platform.

---

### Functions

- `settings_help_str`: Return help string about all available Stty attributes and their possible values on the current platform.
- `settings_help`: Print help message about all available Stty attributes and their possible values on the current platform.

---

## Compatibility

- Requires Python 3.x and a POSIX-like system with the `termios` module.
- Some features depend on platform support (e.g., window size).

---

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

---

## Author

Soumendra Ganguly, 2025

---

## See Also

- [stty(1) manpage](https://man7.org/linux/man-pages/man1/stty.1.html)
- [Python termios documentation](https://docs.python.org/3/library/termios.html)
