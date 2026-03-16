# 🎾 Tennis Champs

A fast-paced 2D tennis game built with Python and Pygame, featuring neon visuals, particle effects, and smart AI.

---

## 🎮 Features

- Smooth mouse-controlled player paddle
- AI opponent with predictive movement and floor-scoop logic
- Neon cyberpunk visuals with glow effects, motion trails, and sparks
- Confetti bursts on scoring and game over
- Sound effects and looping background music
- Score progress bars and animated HUD
- Pause/resume support
- Name entry screen and animated start screen

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Pygame

```bash
pip install pygame
```

### Run the Game

```bash
python tennis_champs_v2.py
```

---

## 📁 Project Structure

```
tennis-champs/
├── tennis_champs_v2.py   # Main game file
├── assets/
│   ├── hit.mp3           # Ball-paddle hit sound
│   ├── score.mp3         # Point scored sound
│   ├── click.mp3         # UI click sound
│   ├── display.mp3       # Victory fanfare
│   └── bk.mp3            # Background music
└── README.md
```

> The game runs without the `assets/` folder — sounds are simply skipped if files are missing.

---

## 🕹️ Controls

| Action | Control |
|---|---|
| Move paddle | Mouse |
| Pause / Resume | `P` key or Pause button |
| Quit to menu | `ESC` |
| Play again | `SPACE` (on game over screen) |

---

## 🏆 How to Win

First player to reach **7 points** wins. The ball gains speed with each paddle hit — don't let it past you!

---

## 🛠️ Built With

- [Python](https://www.python.org/)
- [Pygame](https://www.pygame.org/)

---

## 📄 License

This project is open source and free to use.
