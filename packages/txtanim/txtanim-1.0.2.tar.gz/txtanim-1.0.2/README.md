# txtanim

**Version:** 1.0.2  
**Author:** Neunix Studios  
**License:** MIT  

A powerful terminal text animation library for Python. Enhance your CLI programs with **typewriter effects, blinking text, pulse effects, spinners, loading dots, progress bars, ASCII art (figlet), and matrix-style clear animations**. Perfect for Termux, Linux, macOS, and Windows terminals that support ANSI escape codes.

**Note:** ASCII art functionality uses the [pyfiglet](https://github.com/pwaller/pyfiglet) library, which is licensed under MIT.

---

## Features

### Text Animations
- **Typewriter** – forward and reverse typing effects
- **Blink** – blinking text effect
- **Pulse** – pulse effect between dim and bright text
- **Spinner** – spinner animation
- **Loading Dots** – customizable loading animation
- **Progress Bar** – terminal progress bar with color

### Special Effects
- **Figlet** – bold, filled ASCII art, adapts to terminal width (via `pyfiglet`)
- **Matrix Clear** – vertical falling characters animation that temporarily clears the screen

### Colors
- 8 basic colors (`black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`)
- Dim and bright variations
- Customizable in all animations

### Cursor Handling
- Automatically hides and shows cursor during animations

---

## Installation

```bash
pip install txtanim