"""
============================================================
txtanim - Test file
Author: Neunix Studios
Version: 1.0.2
Purpose: Demonstrate all features of the txtanim module.
Instructions:
- Run this file in a terminal that supports ANSI colors (like Termux, Linux, or macOS terminal).
- Zoom out for full effect of animations like figlet and matrix_clear.
- Ensure 'txtanim' module is installed in your environment.
- figlet fonts may require pyfiglet to be installed.
============================================================
"""

# Import the module
import txtanim

# ============================================================
# FIGLET EFFECT
# ============================================================
# Prints large ASCII art text using pyfiglet.


txtanim.figlet(
    text="WELCOME",
    color="cyan",
    font="slant"  # any pyfiglet font installed in your system
)

# ============================================================
# TYPEWRITER EFFECT
# ============================================================
# Prints text character by character with optional reverse deletion.
txtanim.typewriter(
    text="This is a typewriter animation!",
    speed=0.05,
    reverse=False,
    color="green"
)

# ============================================================
# BLINK EFFECT
# ============================================================
# Makes text blink for a set number of cycles.
txtanim.blink(
    text="Blinking Text",
    cycles=5,
    speed=0.3,
    color="yellow"
)

# ============================================================
# PULSE EFFECT
# ============================================================
# Pulses text between dim and bright.
txtanim.pulse(
    text="Pulsing Text",
    cycles=6,
    speed=0.4,
    color="magenta"
)

# ============================================================
# SPINNER
# ============================================================
# Rotating spinner animation, no text required.
txtanim.spinner(
    cycles=12,
    speed=0.1,
    color="red"
)

# ============================================================
# LOADING DOTS
# ============================================================
# Displays a loading animation with customizable text & symbol.
txtanim.loading_dots(
    text="Loading Module",
    cycles=4,
    speed=0.3,
    color="blue",
    symbol="."
)

# ============================================================
# PROGRESS BAR
# ============================================================
# Shows a terminal progress bar with filled blocks.
txtanim.progress_bar(
    total=20,
    prefix="Progress",
    color="cyan",
    delay=0.1
)

# ============================================================
# MATRIX_CLEAR EFFECT
# ============================================================
# A vertical "matrix rain" animation that clears the screen.
# This hides all previous text temporarily during effect.
txtanim.matrix_clear(
    text="MATRIX MODE ACTIVE",
    speed=0.05,
    density=70,
    color="green"
)

# ============================================================
# INSTRUCTIONS END
# ============================================================
print("\nAll animations executed successfully!")
print("You can re-run the file to see the effects again.")