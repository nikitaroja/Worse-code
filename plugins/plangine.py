import ast
import math
import random
import re
import time


TETRIS_SHAPES = {
    "I": ((0, 1), (1, 1), (2, 1), (3, 1)),
    "O": ((1, 0), (2, 0), (1, 1), (2, 1)),
    "T": ((1, 0), (0, 1), (1, 1), (2, 1)),
    "S": ((1, 0), (2, 0), (0, 1), (1, 1)),
    "Z": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "J": ((0, 0), (0, 1), (1, 1), (2, 1)),
    "L": ((2, 0), (0, 1), (1, 1), (2, 1)),
}
TETRIS_COLORS = {
    "I": "#42d9e8",
    "O": "#f4d43b",
    "T": "#b56cf2",
    "S": "#62d96b",
    "Z": "#f05c64",
    "J": "#5686f2",
    "L": "#f39a45",
}


class TetrisGame:
    def __init__(self, rng=None, columns=10, rows=20):
        self.rng = rng or random.Random()
        self.columns = columns
        self.rows = rows
        self.reset()

    def reset(self):
        self.board = [[None for _ in range(self.columns)] for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.paused = False
        self.game_over = False
        self.current = None
        self.spawn_piece()

    def collides(self, piece, x=None, y=None, cells=None):
        x = piece["x"] if x is None else x
        y = piece["y"] if y is None else y
        cells = piece["cells"] if cells is None else cells
        for cell_x, cell_y in cells:
            board_x, board_y = x + cell_x, y + cell_y
            if board_x < 0 or board_x >= self.columns or board_y >= self.rows:
                return True
            if board_y >= 0 and self.board[board_y][board_x] is not None:
                return True
        return False

    def spawn_piece(self):
        kind = self.rng.choice(tuple(TETRIS_SHAPES))
        self.current = {
            "kind": kind,
            "cells": TETRIS_SHAPES[kind],
            "x": self.columns // 2 - 2,
            "y": -1,
        }
        if self.collides(self.current):
            self.game_over = True

    def move(self, dx, dy=0):
        if self.game_over or self.paused or self.current is None:
            return False
        next_x = self.current["x"] + dx
        next_y = self.current["y"] + dy
        if self.collides(self.current, next_x, next_y):
            if dy > 0:
                self.lock_piece()
            return False
        self.current["x"], self.current["y"] = next_x, next_y
        return True

    def rotate(self):
        if self.game_over or self.paused or self.current is None or self.current["kind"] == "O":
            return False
        cells = self.current["cells"]
        rotated = tuple(sorted((-y, x) for x, y in cells))
        min_x = min(x for x, _ in rotated)
        min_y = min(y for _, y in rotated)
        rotated = tuple((x - min_x, y - min_y) for x, y in rotated)
        for offset in (0, -1, 1, -2, 2):
            if not self.collides(self.current, self.current["x"] + offset, cells=rotated):
                self.current["x"] += offset
                self.current["cells"] = rotated
                return True
        return False

    def hard_drop(self):
        if self.game_over or self.paused or self.current is None:
            return 0
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.score += distance * 2
        return distance

    def lock_piece(self):
        if self.current is None:
            return
        for x, y in self.current["cells"]:
            board_x, board_y = self.current["x"] + x, self.current["y"] + y
            if board_y < 0:
                self.game_over = True
                self.current = None
                return
            self.board[board_y][board_x] = self.current["kind"]
        full_rows = [row for row in self.board if all(cell is not None for cell in row)]
        cleared = len(full_rows)
        if cleared:
            self.board = [row for row in self.board if not all(cell is not None for cell in row)]
            self.board = [[None for _ in range(self.columns)] for _ in range(cleared)] + self.board
            self.score += (0, 100, 300, 500, 800)[cleared] * self.level
            self.lines += cleared
        self.spawn_piece()

    @property
    def level(self):
        return self.lines // 10 + 1

    def tick(self):
        if not self.game_over and not self.paused:
            self.move(0, 1)


def _run_tetris_window(window, canvas, scene):
    game = TetrisGame()
    cell_size = min(28, (scene["height"] - 40) // game.rows, (scene["width"] - 150) // game.columns)
    if cell_size < 10:
        raise ValueError("Tetris needs a window at least 250x240 pixels")

    board_left = 20
    board_top = 20
    board_width = game.columns * cell_size
    board_height = game.rows * cell_size
    side_left = board_left + board_width + 24
    last_fall = time.monotonic()

    def draw_cell(x, y, kind):
        left = board_left + x * cell_size
        top = board_top + y * cell_size
        canvas.create_rectangle(
            left + 1,
            top + 1,
            left + cell_size - 1,
            top + cell_size - 1,
            fill=TETRIS_COLORS[kind],
            outline="#10151d",
        )

    def draw():
        canvas.delete("all")
        canvas.create_rectangle(
            board_left,
            board_top,
            board_left + board_width,
            board_top + board_height,
            fill="#151b24",
            outline="#768397",
            width=2,
        )
        for y, row in enumerate(game.board):
            for x, kind in enumerate(row):
                if kind is not None:
                    draw_cell(x, y, kind)
        if game.current is not None:
            for x, y in game.current["cells"]:
                board_x, board_y = game.current["x"] + x, game.current["y"] + y
                if board_y >= 0:
                    draw_cell(board_x, board_y, game.current["kind"])
        font = (scene["font"], 11)
        canvas.create_text(side_left, board_top + 25, text="PLANGINE", anchor="w", fill="white", font=font)
        canvas.create_text(side_left, board_top + 65, text=f"Score: {game.score}", anchor="w", fill="white", font=font)
        canvas.create_text(side_left, board_top + 95, text=f"Lines: {game.lines}", anchor="w", fill="white", font=font)
        canvas.create_text(side_left, board_top + 125, text=f"Level: {game.level}", anchor="w", fill="white", font=font)
        canvas.create_text(side_left, board_top + 185, text="← →  Move", anchor="w", fill="#c8d2df", font=font)
        canvas.create_text(side_left, board_top + 215, text="↑ / X  Rotate", anchor="w", fill="#c8d2df", font=font)
        canvas.create_text(side_left, board_top + 245, text="↓  Soft drop", anchor="w", fill="#c8d2df", font=font)
        canvas.create_text(side_left, board_top + 275, text="Space  Hard drop", anchor="w", fill="#c8d2df", font=font)
        canvas.create_text(side_left, board_top + 305, text="P  Pause", anchor="w", fill="#c8d2df", font=font)
        canvas.create_text(side_left, board_top + 335, text="R  Restart", anchor="w", fill="#c8d2df", font=font)
        if game.paused:
            canvas.create_text(
                board_left + board_width / 2,
                board_top + board_height / 2,
                text="PAUSED",
                fill="white",
                font=(scene["font"], 22, "bold"),
            )
        elif game.game_over:
            canvas.create_rectangle(
                board_left + 12,
                board_top + board_height / 2 - 34,
                board_left + board_width - 12,
                board_top + board_height / 2 + 34,
                fill="#11161e",
                outline="#f05c64",
                width=2,
            )
            canvas.create_text(
                board_left + board_width / 2,
                board_top + board_height / 2,
                text="GAME OVER\nPress R to restart",
                fill="white",
                font=(scene["font"], 14, "bold"),
                justify="center",
            )

    def on_key(event):
        nonlocal last_fall
        key = event.keysym.lower()
        if key == "r":
            game.reset()
            last_fall = time.monotonic()
        elif key == "p" and not game.game_over:
            game.paused = not game.paused
            last_fall = time.monotonic()
        elif key == "left":
            game.move(-1)
        elif key == "right":
            game.move(1)
        elif key == "down":
            if game.move(0, 1):
                game.score += 1
                last_fall = time.monotonic()
        elif key in ("up", "x"):
            game.rotate()
        elif key == "space":
            game.hard_drop()
            last_fall = time.monotonic()
        draw()

    window.bind("<KeyPress>", on_key)

    def tick():
        nonlocal last_fall
        if not window.winfo_exists():
            return
        now = time.monotonic()
        interval = max(0.12, 0.7 - (game.level - 1) * 0.05)
        if not game.paused and not game.game_over and now - last_fall >= interval:
            game.tick()
            last_fall = now
            draw()
        window.after(16, tick)

    draw()
    window.after(16, tick)
    window.wait_window()


ENTITY_TYPES = {
    "entity_player": {"shape": "rectangle", "color": "red", "width": 28, "height": 28},
    "entity_block": {"shape": "rectangle", "color": "gray", "width": 36, "height": 36},
    "entity_circle": {"shape": "oval", "color": "deepskyblue", "width": 32, "height": 32},
    "entity_enemy": {"shape": "triangle", "color": "purple", "width": 34, "height": 34},
    "entity_coin": {"shape": "oval", "color": "gold", "width": 22, "height": 22},
}


def _unquote(value):
    value = value.strip()
    if value[:1] in ("'", '"'):
        try:
            result = ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise ValueError(f"invalid quoted value: {value}") from error
        if not isinstance(result, str):
            raise ValueError("expected text")
        return result
    return value


def register(wc):
    scene = {}

    def require_segment():
        if not scene.get("loaded"):
            raise ValueError("use 'Plangine-load plangine' before a Plangine segment")
        if not scene.get("inside"):
            raise ValueError("Plangine commands must be between planginestarthere and planginend")

    def no_arguments(rest, usage):
        if rest.strip():
            raise ValueError(f"use: {usage}")

    def load(ctx, rest):
        if rest.strip().lower() != "plangine":
            raise ValueError("use: Plangine-load plangine")
        if scene.get("inside"):
            raise ValueError("cannot load Plangine inside a segment")
        scene["loaded"] = True

    def start(ctx, rest):
        no_arguments(rest, "planginestarthere")
        if not scene.get("loaded"):
            raise ValueError("use 'Plangine-load plangine' first")
        if scene.get("inside"):
            raise ValueError("Plangine segments cannot be nested")
        scene.update({
            "inside": True,
            "width": 800,
            "height": 600,
            "bg": "white",
            "font": "Arial",
            "entities": [],
            "triggers": [],
            "edge_behavior": {},
            "game": None,
        })

    def create_window(ctx, rest):
        require_segment()
        parts = [part.strip() for part in rest.split("]")]
        if not parts or not parts[0]:
            raise ValueError("use: createwindow]800x600]bg white]textfont Arial")
        match = re.fullmatch(r"(\d+)\s*[xX]\s*(\d+)", parts[0])
        if not match:
            raise ValueError("window resolution must look like 800x600")
        width, height = (int(value) for value in match.groups())
        if not 100 <= width <= 4096 or not 100 <= height <= 4096:
            raise ValueError("window dimensions must be between 100 and 4096 pixels")
        scene["width"], scene["height"] = width, height
        for option in parts[1:]:
            key, separator, value = option.partition(" ")
            value = _unquote(value)
            if not separator or not value:
                raise ValueError(f"invalid window option: {option}")
            if key == "bg":
                scene["bg"] = value
            elif key == "textfont":
                scene["font"] = value
            else:
                raise ValueError(f"unknown window option: {key}")

    def create_entity(entity_type):
        def handler(ctx, rest):
            require_segment()
            parts = [part.strip() for part in rest.split("]")]
            if not parts or not parts[0]:
                raise ValueError(f"use: create-{entity_type}]x,y]moveto-wasd-arrow")
            position = parts[0].lower()
            if position == "center":
                x, y = scene["width"] / 2, scene["height"] / 2
            else:
                coordinates = position.split(",")
                if len(coordinates) != 2:
                    raise ValueError("entity position must be x,y or center")
                try:
                    x, y = (float(value.strip()) for value in coordinates)
                except ValueError as error:
                    raise ValueError("entity position must contain two numbers") from error
            template = ENTITY_TYPES[entity_type]
            entity = {
                "kind": entity_type,
                "shape": template["shape"],
                "color": template["color"],
                "width": template["width"],
                "height": template["height"],
                "x": x,
                "y": y,
                "mode": "locked",
                "speed": 0.0,
                "wac": False,
                "alive": True,
            }
            for option in parts[1:]:
                option = option.strip()
                if option.startswith("id="):
                    entity["id"] = option[3:].strip()
                    if not entity["id"].isidentifier():
                        raise ValueError("entity id must be a valid name")
                    continue
                if option == "moveto-locked":
                    entity["mode"] = "locked"
                elif option == "moveto-wasd-arrow":
                    entity["mode"] = "manual"
                elif option == "wac":
                    entity["wac"] = True
                else:
                    match = re.fullmatch(r"moveto-auto(\d+(?:\.\d+)?)kmh", option)
                    if not match:
                        raise ValueError(f"unknown entity option: {option}")
                    entity["mode"] = "auto"
                    entity["speed"] = float(match.group(1)) * 10
            if entity_type == "entity_player" and any(
                item["kind"] == "entity_player" for item in scene["entities"]
            ):
                raise ValueError("only one entity_player is supported in Plangine 1a")
            if "id" not in entity:
                entity["id"] = entity_type
                suffix = 2
                while any(item["id"] == entity["id"] for item in scene["entities"]):
                    entity["id"] = f"{entity_type}_{suffix}"
                    suffix += 1
            elif any(item["id"] == entity["id"] for item in scene["entities"]):
                raise ValueError(f"duplicate entity id: {entity['id']}")
            scene["entities"].append(entity)

        return handler

    def change_color(ctx, rest):
        require_segment()
        parts = [part.strip() for part in rest.split("]")]
        if len(parts) != 2 or not all(parts):
            raise ValueError("use: changecolor]entity_id]color")
        entity = next((item for item in scene["entities"] if item["id"] == parts[0]), None)
        if entity is None:
            raise ValueError(f"entity not found: {parts[0]}")
        entity["color"] = _unquote(parts[1])

    def kill(ctx, rest):
        require_segment()
        parts = [part.strip() for part in rest.split("]")]
        if len(parts) != 2 or parts[1] != "edgeofwindow":
            raise ValueError("use: kill]entity_id]edgeofwindow")
        if not any(item["id"] == parts[0] for item in scene["entities"]):
            raise ValueError(f"entity not found: {parts[0]}")
        scene["edge_behavior"][parts[0]] = "kill"

    def create_trigger(ctx, rest):
        require_segment()
        parts = rest.split("]", 3)
        if len(parts) != 3:
            raise ValueError('use: create-trigger]x,y,width,height]once|repeat|count]say "text"')
        coordinates = [value.strip() for value in parts[0].split(",")]
        if len(coordinates) != 4:
            raise ValueError("trigger bounds must be x,y,width,height")
        try:
            x, y, width, height = (float(value) for value in coordinates)
        except ValueError as error:
            raise ValueError("trigger bounds must contain four numbers") from error
        if width <= 0 or height <= 0:
            raise ValueError("trigger width and height must be positive")
        frequency = parts[1].strip().lower()
        if frequency == "once":
            remaining = 1
        elif frequency == "repeat":
            remaining = None
        else:
            try:
                remaining = int(frequency)
            except ValueError as error:
                raise ValueError("trigger frequency must be once, repeat, or a positive count") from error
            if remaining < 1:
                raise ValueError("trigger count must be positive")
        action = parts[2].strip()
        if not action:
            raise ValueError("trigger action cannot be empty")
        scene["triggers"].append({
            "x": x, "y": y, "width": width, "height": height,
            "remaining": remaining, "action": action, "inside": False,
        })

    def run_action(action):
        command, separator, rest = action.partition(" ")
        rest = rest.strip() if separator else ""
        if command in (wc.cfg.get("say", "say"), "say"):
            if not rest:
                raise ValueError("trigger say action needs an expression")
            wc.ctx.out(wc.ctx.ev(rest))
        elif command in (wc.cfg.get("set", "set"), "set"):
            target, separator, expression = rest.partition("=")
            target = target.strip()
            if not separator or not target.isidentifier():
                raise ValueError("trigger set action must look like: set name = expression")
            wc.variables[target] = wc.ctx.ev(expression)
        elif command in (wc.cfg.get("do", "do"), "do"):
            if not rest:
                raise ValueError("trigger do action needs an expression")
            wc.ctx.ev(rest)
        elif command in wc.commands:
            wc.commands[command](wc.ctx, rest)
        else:
            raise ValueError(f"unsupported trigger action: {command}")

    def run_scene():
        import tkinter as tk
        from tkinter import messagebox

        if scene["triggers"] and not any(
            entity["kind"] == "entity_player" for entity in scene["entities"]
        ):
            raise ValueError("Plangine triggers require an entity_player")
        root = getattr(tk, "_default_root", None)
        window = tk.Toplevel(root) if root is not None else tk.Tk()
        window.title("Plangine 1a")
        window.resizable(False, False)
        canvas = tk.Canvas(
            window,
            width=scene["width"],
            height=scene["height"],
            bg=scene["bg"],
            highlightthickness=0,
        )
        canvas.pack()
        if scene["game"] == "tetris":
            _run_tetris_window(window, canvas, scene)
            scene["window"] = None
            return
        pressed = set()
        last_time = time.monotonic()
        stopped = False

        def close():
            nonlocal stopped
            stopped = True
            if window.winfo_exists():
                window.destroy()

        def key_down(event):
            key = event.keysym.lower()
            if key in ("w", "a", "s", "d", "up", "down", "left", "right"):
                pressed.add(key)

        def key_up(event):
            pressed.discard(event.keysym.lower())

        window.bind("<KeyPress>", key_down)
        window.bind("<KeyRelease>", key_up)
        window.protocol("WM_DELETE_WINDOW", close)

        def overlaps(entity, trigger):
            left = entity["x"] - entity["width"] / 2
            right = entity["x"] + entity["width"] / 2
            top = entity["y"] - entity["height"] / 2
            bottom = entity["y"] + entity["height"] / 2
            return (
                right >= trigger["x"]
                and left <= trigger["x"] + trigger["width"]
                and bottom >= trigger["y"]
                and top <= trigger["y"] + trigger["height"]
            )

        def draw():
            canvas.delete("all")
            for trigger in scene["triggers"]:
                canvas.create_rectangle(
                    trigger["x"],
                    trigger["y"],
                    trigger["x"] + trigger["width"],
                    trigger["y"] + trigger["height"],
                    outline="green",
                    dash=(5, 3),
                    width=2,
                )
            for entity in scene["entities"]:
                if not entity["alive"]:
                    continue
                x, y = entity["x"], entity["y"]
                half_width, half_height = entity["width"] / 2, entity["height"] / 2
                bounds = (x - half_width, y - half_height, x + half_width, y + half_height)
                if entity["shape"] == "triangle":
                    canvas.create_polygon(
                        x, y - half_height, x - half_width, y + half_height,
                        x + half_width, y + half_height, fill=entity["color"],
                    )
                else:
                    draw_shape = canvas.create_rectangle if entity["shape"] == "rectangle" else canvas.create_oval
                    draw_shape(*bounds, fill=entity["color"], outline="")
                canvas.create_text(
                    x, y + half_height + 10, text=entity["id"], fill="black",
                    font=(scene["font"], 9),
                )

        def tick():
            nonlocal last_time
            if stopped:
                return
            now = time.monotonic()
            delta = min(now - last_time, 0.05)
            last_time = now
            player = next(
                (entity for entity in scene["entities"] if entity["kind"] == "entity_player" and entity["alive"]),
                None,
            )
            for entity in scene["entities"]:
                if not entity["alive"] or entity["mode"] == "locked":
                    continue
                keys = pressed if entity["mode"] == "manual" or entity["wac"] else set()
                dx = int("d" in keys or "right" in keys) - int("a" in keys or "left" in keys)
                dy = int("s" in keys or "down" in keys) - int("w" in keys or "up" in keys)
                if dx == 0 and dy == 0:
                    dx = 1 if entity["mode"] == "auto" else 0
                length = math.hypot(dx, dy)
                if length:
                    speed = entity["speed"] if entity["mode"] == "auto" and not keys else 180
                    entity["x"] += dx / length * speed * delta
                    entity["y"] += dy / length * speed * delta
            for entity in scene["entities"]:
                if not entity["alive"]:
                    continue
                outside = (
                    entity["x"] - entity["width"] / 2 < 0
                    or entity["y"] - entity["height"] / 2 < 0
                    or entity["x"] + entity["width"] / 2 > scene["width"]
                    or entity["y"] + entity["height"] / 2 > scene["height"]
                )
                if outside and scene["edge_behavior"].get(entity["id"]) == "kill":
                    entity["alive"] = False
                else:
                    entity["x"] = min(max(entity["x"], entity["width"] / 2), scene["width"] - entity["width"] / 2)
                    entity["y"] = min(max(entity["y"], entity["height"] / 2), scene["height"] - entity["height"] / 2)
            if player and player["alive"]:
                for trigger in scene["triggers"]:
                    inside = overlaps(player, trigger)
                    if inside and not trigger["inside"] and trigger["remaining"] != 0:
                        if trigger["remaining"] is not None:
                            trigger["remaining"] -= 1
                        try:
                            run_action(trigger["action"])
                        except Exception as error:
                            messagebox.showerror("Plangine trigger error", str(error), parent=window)
                            close()
                            return
                    trigger["inside"] = inside
            draw()
            window.after(16, tick)

        draw()
        window.after(16, tick)
        window.wait_window()
        scene["window"] = None

    def tetris(ctx, rest):
        no_arguments(rest, "tetris")
        require_segment()
        if scene["entities"] or scene["triggers"]:
            raise ValueError("tetris mode cannot be combined with entities or triggers")
        scene["game"] = "tetris"

    def end(ctx, rest):
        no_arguments(rest, "planginend")
        require_segment()
        scene["inside"] = False
        run_scene()

    def register_command(key, default, handler):
        wc.command(key, default, handler)

    for key, default, handler in (
        ("Plangine-load", "Plangine-load", load),
        ("planginestarthere", "planginestarthere", start),
        ("planginend", "planginend", end),
        ("createwindow", "createwindow", create_window),
        ("changecolor", "changecolor", change_color),
        ("kill", "kill", kill),
        ("create-trigger", "create-trigger", create_trigger),
        ("tetris", "tetris", tetris),
    ):
        register_command(key, default, handler)
    for entity_type in ENTITY_TYPES:
        register_command(f"create-{entity_type}", f"create-{entity_type}", create_entity(entity_type))
