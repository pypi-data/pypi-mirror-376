# txtanim.py

import sys, time, shutil, os, random
import pyfiglet

#=========Screen Width============
width = shutil.get_terminal_size().columns

# ===== Colors =====
RESET = "\033[0m"
BRIGHT = "\033[1m"
DIM = "\033[2m"

COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

def _parse_color(color: str):
    if not color:
        return ""
    return COLORS.get(color.lower(), "")

# ===== Cursor & Screen helpers =====
def _hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def _show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# ===== Animations =====

def typewriter(text: str, speed: float = 0.1, reverse: bool = False, color: str = None):
    """Typewriter effect. If reverse=True, text deletes itself."""
    color_code = _parse_color(color)
    reset = RESET if color else ""

    _hide_cursor()
    try:
        if not reverse:
            for ch in text:
                sys.stdout.write(color_code + ch + reset)
                sys.stdout.flush()
                time.sleep(speed)
        else:
            sys.stdout.write(color_code + text + reset)
            sys.stdout.flush()
            time.sleep(speed)
            for i in range(len(text), 0, -1):
                sys.stdout.write("\r" + color_code + text[:i-1] + " " * (len(text)-i+1) + reset)
                sys.stdout.flush()
                time.sleep(speed)
        print()
    finally:
        _show_cursor()

def blink(text: str, cycles: int = 5, speed: float = 0.5, color: str = None):
    """Blinking text."""
    color_code = _parse_color(color)
    reset = RESET if color else ""

    _hide_cursor()
    try:
        for _ in range(cycles):
            sys.stdout.write("\r" + color_code + text + reset)
            sys.stdout.flush()
            time.sleep(speed)
            sys.stdout.write("\r" + " " * len(text))
            sys.stdout.flush()
            time.sleep(speed)
        print()
    finally:
        _show_cursor()

def pulse(text: str, cycles: int = 5, speed: float = 0.3, color: str = None):
    """Pulse between dim and bright text."""
    color_code = _parse_color(color)
    reset = RESET if color else ""

    _hide_cursor()
    try:
        for _ in range(cycles):
            sys.stdout.write("\r" + DIM + color_code + text + reset)
            sys.stdout.flush()
            time.sleep(speed)
            sys.stdout.write("\r" + BRIGHT + color_code + text + reset)
            sys.stdout.flush()
            time.sleep(speed)
        print()
    finally:
        _show_cursor()

def spinner(cycles: int = 10, speed: float = 0.1, color: str = None, frames: list = None):
    """Spinner animation (no text)."""
    if frames is None:
        frames = ["|", "/", "-", "\\"]
    color_code = _parse_color(color)
    reset = RESET if color else ""

    _hide_cursor()
    try:
        for _ in range(cycles):
            for ch in frames:
                sys.stdout.write("\r" + color_code + ch + reset)
                sys.stdout.flush()
                time.sleep(speed)
        print()
    finally:
        _show_cursor()

def loading_dots(text: str = "Loading", cycles: int = 5, speed: float = 0.3, color: str = None, symbol: str = "."):
    """Loading dots animation with customizable text & symbol."""
    color_code = _parse_color(color)
    reset = RESET if color else ""

    _hide_cursor()
    try:
        for _ in range(cycles):
            for i in range(4):  # "", ".", "..", "..."
                dots = symbol * i
                padding = " " * (3 - i)
                sys.stdout.write(f"\r{color_code}{text}{dots}{reset}{padding}")
                sys.stdout.flush()
                time.sleep(speed)
        print()
    finally:
        _show_cursor()

def progress_bar(total: int = 20, prefix: str = "Progress", color: str = None, delay: float = 0.1):
    """Progress bar animation."""
    width = shutil.get_terminal_size().columns - len(prefix) - 10
    width = max(width, 10)
    color_code = _parse_color(color)
    reset = RESET if color else ""

    _hide_cursor()
    try:
        for i in range(total + 1):
            filled = int(width * i / total)
            bar = "█" * filled + "-" * (width - filled)
            sys.stdout.write(f"\r{prefix} |{color_code}{bar}{reset}| {i}/{total}")
            sys.stdout.flush()
            time.sleep(delay)
        print()
    finally:
        _show_cursor()

def figlet(text: str, font: str = "slant", color: str = None,width = width):
    """Render ASCII art text using pyfiglet."""
    color_code = _parse_color(color)
    reset = RESET if color else ""
    ascii_text = pyfiglet.figlet_format(text, font=font)
    print(color_code + ascii_text + reset)

def matrix_clear(chars: str = "0123",speed: float = 0.05, density: float = 0.02, color: str = "green",duration: float = 5,):
    """
    Full-screen Matrix rain effect.
    - duration: total time to run (seconds)
    - speed: lower = faster fall
    - density: probability of starting a new stream (0.01 - 0.2 recommended)
    - color: rain color (default green)
    - chars: character set for rain
    """
    width = shutil.get_terminal_size().columns
    height = shutil.get_terminal_size().lines
    color_code = _parse_color(color)
    reset = RESET if color else ""

    streams = [0] * width

    _hide_cursor()
    _clear_screen()
    try:
        start = time.time()
        while time.time() - start < duration:
            frame = []
            for col in range(width):
                if streams[col] > 0:
                    frame.append(color_code + random.choice(chars) + reset)
                    streams[col] -= 1
                elif random.random() < density:
                    streams[col] = random.randint(3, height // 2)
                    frame.append(color_code + random.choice(chars) + reset)
                else:
                    frame.append(" ")
            print("".join(frame))
            time.sleep(speed)
    finally:
        _clear_screen()
        _show_cursor()

# ===== Public API =====
__all__ = [
    "typewriter",
    "blink",
    "pulse",
    "spinner",
    "loading_dots",
    "progress_bar",
    "figlet",
    "matrix_clear",
]