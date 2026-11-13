# Plangine 1a

[Русская версия](PLANGINE_1A.ru.md)

Plangine is a plugin for making simple 2D games with Tkinter. Install it into a project with the plugin manager:

```powershell
python wc_plugin_manager.py "path\to\your_project" --install plangine
```

Python with Tkinter is required to open game windows. Put Plangine commands inside a segment bounded by `planginestarthere` and `planginend`. The game window opens when `planginend` runs; the WC program continues after you close the window.

## Your first game

```text
Plangine-load plangine
planginestarthere
createwindow]800x600]bg white]textfont Arial
create-entity_player]50,50]moveto-wasd-arrow
create-entity_block]300,200
create-entity_circle]400,300]id=orb]moveto-locked
create-entity_enemy]600,200
create-entity_coin]700,400
changecolor]entity_player]black
planginend
```

## Commands

- `Plangine-load plangine` loads the plugin before a game segment.
- `planginestarthere` begins a segment. `planginend` ends it and opens the game window. Segments cannot be nested.
- `createwindow]widthxheight]bg color]textfont font` sets up the window. For example: `createwindow]800x600]bg "#f0f0f0"]textfont Arial`. Each dimension must be between 100 and 4096 pixels.
- `create-entity_player]x,y]mode` creates a red player. Use `center` instead of `x,y` to place it in the middle of the window.
- `create-entity_block`, `create-entity_circle`, `create-entity_enemy`, and `create-entity_coin` create a gray block, a blue circle, a purple enemy, and a gold coin.
- Add `id=name` to any entity to refer to it in other commands. Default IDs are `entity_player`, `entity_block`, `entity_block_2`, and so on. Plangine 1a supports one player.
- `changecolor]entity_id]color` changes an entity's color, for example `changecolor]entity_player]black`.
- `kill]entity_id]edgeofwindow` removes an entity when it leaves the window. Without this command, entities stop at the edge.

## Movement

Choose one movement mode for an entity:

- `moveto-wasd-arrow` — control with WASD or the arrow keys at 180 pixels per second.
- `moveto-locked` — the entity does not move (the default).
- `moveto-auto10kmh` — automatically moves the entity to the right at 10 km/h. Add `]wac` to allow keyboard movement while it moves automatically, for example: `create-entity_player]center]moveto-auto10kmh]wac`. In Plangine 1a, 1 km/h is treated as 10 pixels per second.

## Triggers

A trigger runs when the player enters its rectangle. Touching the rectangle's boundary also counts as entering it:

```text
create-trigger]300,200,100,100]once]say "You entered the area!"
```

The parameters are `x,y,width,height`, a trigger limit, and a command to run on entry. The limit can be `once` (one time), `repeat` (every new entry), or a positive number (the maximum number of entries). Triggers are outlined with a green dashed line.

A trigger action is one command:

- `say expression` — print a value.
- `set name = expression` — update a WC variable.
- `do expression` — evaluate a WC expression.
- A command from an installed plugin, for example `play /sounds/coin.wav`.

Trigger actions accept the standard `say`, `set`, and `do` commands, as well as their configured command words. Outside triggers, use the command words from your `wc_config.json` if you have renamed them.

Example score counter:

```text
set score = 0
Plangine-load plangine
planginestarthere
createwindow]800x600]bg white]textfont Arial
create-entity_player]50,50]moveto-wasd-arrow
create-trigger]300,200,100,100]3]set score = score + 1
planginend
say score
```

The score is printed after the game window closes.

## Tetris demo

The project includes `demos\PlangineTetris\start.wc`. Run it from the Worse Code project root:

```powershell
python wc.py demos\PlangineTetris\start.wc
```

Inside a segment, the `tetris` command starts a ready-to-play example: Left/Right moves a piece, Down speeds it up, Up or `X` rotates it, Space hard-drops it, `P` pauses, and `R` restarts after game over. This mode cannot be combined with entities or triggers in the same segment. The game rules are implemented in the `TetrisGame` class in `plugins\plangine.py`; see `demos\PlangineTetris\README.md` for a short walkthrough.
