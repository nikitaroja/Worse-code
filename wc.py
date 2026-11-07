# This is generic wc.py initiator. You can change this file to your project by wc.py viewer or by hand.
# If you want to you can sign here your project name:Legaccalc :D
# Language of initiator: ENGLISH
# L E G A C C A L C
import sys
import os
import json
import math
import time
import random
from datetime import datetime
# All the imports

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "wc_config.json")
# Defaults down here!

DEFAULTS = {
    "say": "say",
    "set": "set",
    "ask": "ask",
    "if": "if",
    "else": "else",
    "end": "end",
    "while": "makeuserdoright",
    "for": "draw",
    "break": "forcequit",
    "do": "make",
    "canvas": "minipaint",
    "text": "speaksymbols",
    "load": "load",
    "gui_start": "wcsgstart",
    "gui_stop": "wcsgstophere",
    "force_noecho": "force_noecho",
    "comment": "#",
    "prompt": "> ",
}

GUI_MODULE_NAMES = ("standrt_gui", "standart_gui")

class BlockError(Exception):
    def __init__(self, number, message):
        super().__init__(message)
        self.number = number

def load_config(program_dir=None):
    cfg = dict(DEFAULTS)
    paths = [CONFIG_PATH]
    if program_dir:
        paths.append(os.path.join(program_dir, "wc_config.json"))
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return cfg

def show(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value

def read_value(text):
    for convert in (int, float):
        try:
            value = convert(text)
        except ValueError:
            continue
        if isinstance(value, float) and not math.isfinite(value):
            break
        return value
    return text

def strip_comment(line, comment):
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif line.startswith(comment, i):
            return line[:i]
        i += 1
    return line

def build_blocks(program, cfg):
    openers = {cfg["if"]: "if", cfg["while"]: "while", cfg["for"]: "for"}
    kinds, end_at, else_at, opener_of = {}, {}, {}, {}
    stack = []
    for index, (number, line) in enumerate(program):
        word = line.partition(" ")[0]
        if word in openers:
            kinds[index] = openers[word]
            stack.append(index)
        elif word == cfg["else"]:
            if not stack or kinds[stack[-1]] != "if" or stack[-1] in else_at:
                raise BlockError(number, f'{cfg["else"]} without {cfg["if"]}')
            else_at[stack[-1]] = index
            opener_of[index] = stack[-1]
        elif word == cfg["end"]:
            if not stack:
                raise BlockError(number, f'{cfg["end"]} without a block')
            opener = stack.pop()
            end_at[opener] = index
            opener_of[index] = opener
    if stack:
        number = program[stack[-1]][0]
        raise BlockError(number, f'unclosed block {cfg[kinds[stack[-1]]]} (missing {cfg["end"]})')
    return kinds, end_at, else_at, opener_of

def run_program(lines, cfg, program_dir):
    variables = {
        "year": datetime.now().year,
        "random": random.randint
    }
    gui = None
    in_gui = False
    force_noecho = False
    canvas_words = {
        cfg["canvas"]: "canvas_open",
        "clear": "canvas_clear",
        "rect": "canvas_rect",
        "circle": "canvas_circle",
        cfg["text"]: "canvas_text",
    }

    def ev(expression):
        return eval(expression, variables)

    def use_gui_console():
        return gui is not None and (in_gui or force_noecho)

    def out(value):
        if use_gui_console():
            gui.console_print(value)
        else:
            print(value)

    def fail(message):
        if gui is not None:
            gui.set_terminal_visible(True)
        print(message)

    program = []
    for number, raw in enumerate(lines, start=1):
        line = strip_comment(raw, cfg["comment"]).strip()
        if line:
            program.append((number, line))

    try:
        kinds, end_at, else_at, opener_of = build_blocks(program, cfg)
    except BlockError as error:
        print(f"Error on line {error.number}: {error}")
        return

    pc = 0
    loops = []

    try:
        while pc < len(program):
            number, line = program[pc]
            here = pc
            pc += 1
            word, _, rest = line.partition(" ")
            # Elif's

            try:
                if word == cfg["if"]:
                    if not ev(rest):
                        pc = else_at[here] + 1 if here in else_at else end_at[here] + 1
                elif word == cfg["else"]:
                    pc = end_at[opener_of[here]] + 1
                elif word == cfg["end"]:
                    opener = opener_of[here]
                    if kinds[opener] != "if":
                        pc = opener
                elif word == cfg["while"]:
                    top = loops[-1] if loops and loops[-1]["start"] == here else None
                    if ev(rest):
                        if top is None:
                            loops.append({"start": here})
                    else:
                        if top is not None:
                            loops.pop()
                        pc = end_at[here] + 1
                elif word == cfg["for"]:
                    name, separator, source = rest.partition(" in ")
                    if not separator or not name.strip().isidentifier():
                        raise ValueError(f'use: {cfg["for"]} name in list')
                    top = loops[-1] if loops and loops[-1]["start"] == here else None
                    if top is None:
                        top = {"start": here, "items": list(ev(source)), "pos": 0}
                        loops.append(top)
                    if top["pos"] < len(top["items"]):
                        variables[name.strip()] = top["items"][top["pos"]]
                        top["pos"] += 1
                    else:
                        loops.pop()
                        pc = end_at[here] + 1
                elif word == cfg["break"]:
                    if not loops:
                        raise ValueError(f'{cfg["break"]} outside of a loop')
                    pc = end_at[loops.pop()["start"]] + 1
                elif word == cfg["load"]:
                    name = rest.strip()
                    if name.lower() not in GUI_MODULE_NAMES:
                        raise ValueError(f"Unknown module '{name}'. Available: standrt_gui")
                    if gui is None:
                        try:
                            import wcsg as gui_module
                        except ImportError as error:
                            raise ValueError(f"Could not load WCSG: {error}")
                        gui = gui_module
                        variables["waitkey"] = gui.waitkey
                elif word == cfg["gui_start"]:
                    if gui is None:
                        raise ValueError(f'Load WCSG first: {cfg["load"]} standrt_gui')
                    in_gui = True
                    gui.set_terminal_visible(False)
                elif word == cfg["gui_stop"]:
                    if not in_gui:
                        raise ValueError(f'{cfg["gui_stop"]} without {cfg["gui_start"]}')
                    in_gui = False
                    gui.console_finish()
                    gui.canvas_finish()
                    if not force_noecho:
                        gui.set_terminal_visible(True)
                elif word == cfg["force_noecho"]:
                    if gui is None:
                        raise ValueError(f'Load WCSG first: {cfg["load"]} standrt_gui')
                    force_noecho = True
                    gui.set_terminal_visible(False)
                elif word == cfg["say"]:
                    out(show(ev(rest)))
                elif word == cfg["set"]:
                    target, separator, value = rest.partition("=")
                    if not separator:
                        raise ValueError(f'use: {cfg["set"]} name = value')
                    target = target.strip()
                    result = ev(value)
                    if target.isidentifier():
                        variables[target] = result
                    else:
                        variables["__value"] = result
                        try:
                            exec(f"{target} = __value", variables)
                        finally:
                            variables.pop("__value", None)
                elif word == cfg["do"]:
                    ev(rest)
                elif word == cfg["ask"]:
                    if use_gui_console():
                        answer = gui.console_ask(cfg["prompt"])
                    else:
                        answer = input(cfg["prompt"])
                    variables[rest.strip()] = read_value(answer)
                elif word == "sleep":
                    seconds = float(ev(rest))
                    if gui is not None and gui.has_windows():
                        gui.sleep(seconds)
                    else:
                        time.sleep(seconds)
                elif word == "exit" or word == "quit":
                    sys.exit()
                elif word in canvas_words:
                    if gui is None:
                        raise ValueError(f'Load WCSG first: {cfg["load"]} standrt_gui')
                    if not in_gui:
                        raise ValueError(f'{word} goes between {cfg["gui_start"]} and {cfg["gui_stop"]}')
                    arguments = ev("(" + rest + ",)") if rest.strip() else ()
                    try:
                        getattr(gui, canvas_words[word])(*arguments)
                    except TypeError as error:
                        raise ValueError(f"Wrong arguments for '{word}': {error}")
                elif in_gui:
                    gui.run_line(line, variables, program_dir, read_value)
                elif gui is not None and word.lower() in gui.PRESETS:
                    raise ValueError(f'WCSG windows go between {cfg["gui_start"]} and {cfg["gui_stop"]}')
                else:
                    out(f"WC does not understand: {line}")
            except Exception as error:
                fail(f"Error on line {number}: {error}")
                return

        if in_gui:
            fail(f'Error: {cfg["gui_start"]} zone is not closed (missing {cfg["gui_stop"]})')
    finally:
        if gui is not None:
            gui.shutdown()

def main():
    pause = "--pause" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--pause"]

    if not args:
        print("Usage: python wc.py file.wc")
        return

    cfg = load_config(os.path.dirname(os.path.abspath(args[0])))

    try:
        with open(args[0], encoding="utf-8-sig") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {args[0]}")
    else:
        run_program(lines, cfg, os.path.dirname(os.path.abspath(args[0])))

    if pause:
        input("\nPress Enter to close window...")

if __name__ == "__main__":
    main()
