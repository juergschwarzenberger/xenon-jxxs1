# Xenon Vertical Space Arcade Game

A retro-inspired vertical scrolling shooter built with [Pygame](https://www.pygame.org/).
Command the Xenon starfighter through successive enemy armadas, unlock
progressively stronger weapon systems, and defeat a level boss to
advance.

## Features

- Three handcrafted stages with unique enemy palettes and behaviors.
- Progressive weapon unlocks: pulse cannon, twin blaster, and an
  explosive spread shot.
- Reactive enemy AI that fires back and bosses that barrage the screen
  with bullet patterns.
- Score tracking, player health display, and level intro overlays.
- Simple keyboard controls suitable for laptops and desktop PCs.

## Requirements

- Python 3.10+
- `pygame` 2.5 or later

Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python src/xenon_game.py
```

### Controls

- **Arrow Keys** – Move the Xenon starfighter.
- **Space** – Fire the currently equipped weapon.
- **R** – Restart after defeat.
- **Esc** – Quit the game.

## Development Notes

The gameplay systems live in [`src/xenon_game.py`](src/xenon_game.py).
All sprites are rendered with simple primitives to keep the repository
asset-free.  Extend the `LevelDefinition` list to add more stages, or
customize the `Weapon` definitions to create unique play styles.
