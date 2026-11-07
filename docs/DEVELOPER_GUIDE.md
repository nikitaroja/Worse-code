# Developer Guide

How Worse Code works inside and how to extend it. [Русская версия](DEVELOPER_GUIDE.ru.md)

## 1. Repository layout

```
wc.py                  the interpreter (config, block matching, execution loop)
wcsg.py                WCSG module: windows, black console, canvas (needs tkinter)
wc_modifier.py         WC Service Modifier: settings window (tkinter, Russian UI)
wc_exe_maker.py        builds a Windows .exe for a program folder (PyInstaller)
wc_config.example.json every config key with its default word
examples/              small programs, each folder has a start.wc
projects/              your own programs
docs/                  this guide
```

`wcsg.py` is imported only by `load`, so programs that do not use windows never need tkinter.

## 2. Design in one page

- **Line based.** A program is a list of `(line_number, text)` after comments and blank lines are removed. The first word of a line is the command, the rest is its argument.
- **Expressions are Python.** The argument of most commands goes through `eval(expression, variables)`. The `variables` dict is the *globals* of `eval`, which also lets comprehensions see every variable. It holds the program variables plus `year`, `random` and (after `load`) `waitkey`.
- **Blocks are matched before running.** `build_blocks` walks the program once and records where every `if`, loop, `else` and `end` belong. The execution loop then jumps with a program counter, so loops are just "jump back".
- **Keywords come from a config.** Code never compares against literal `"say"`, it compares against `cfg["say"]`. Only a few words are fixed: `sleep`, `exit`, `quit`, `clear`, `rect`, `circle`.
- **GUI is a plug-in.** `wc.py` talks to `wcsg.py` through a handful of functions (see section 4).

## 3. wc.py

| Piece | Job |
|---|---|
| `DEFAULTS` | every configurable keyword and its default word |
| `load_config(program_dir)` | layers: `DEFAULTS`, then `wc_config.json` next to `wc.py`, then `wc_config.json` next to the program |
| `strip_comment` | removes a comment but ignores the comment symbol inside quotes |
| `read_value` | `ask` conversion: `int`, then `float`, otherwise text |
| `build_blocks` | returns `kinds`, `end_at`, `else_at`, `opener_of` (index maps) and raises `BlockError` with a line number |
| `run_program` | the execution loop |
| `main` | arguments (`--pause`), file reading, calls `run_program` |

**Block tables.** Indexes point into the `program` list. `kinds[i]` is `"if"`, `"while"` or `"for"` for an opener at `i`. `end_at[i]` is the index of its `end`, `else_at[i]` the index of its `else`, `opener_of[j]` maps an `else` or `end` back to its opener.

**Execution loop.** `pc` is the program counter. At each step `here = pc; pc += 1`, then the command runs and may overwrite `pc`:

- `if`: when false, jump to the line after `else`, or after `end`.
- `else`: reached only from the true branch, so jump past the `end`.
- `end`: for `while` and `for`, jump back to the opener, which re-checks the condition.
- loops keep a stack `loops` of dicts (`start`, and for `for` also `items`, `pos`). The opener sees `loops[-1]["start"] == here` on re-entry and continues the same loop.
- `break` pops the top loop and jumps past its `end`.

**Dispatch order** in the `try` chain matters: block words first, then `load` and the GUI zone words, then `say / set / do / ask / sleep / exit`, then canvas words, then window lines (only inside a zone), and last the "does not understand" fallback.

**Console routing.** `use_gui_console()` is true inside a zone or after `force_noecho`. `out()` and `ask` use it to choose between `print` / `input` and `gui.console_print` / `gui.console_ask`. `fail()` shows the real console again before printing an error, otherwise a hidden console would swallow it.

**`set` trick.** A plain name is stored directly. Anything else (`a[0]`, `a, b`) goes through `exec(f"{target} = __value", variables)` with the value stored temporarily as `__value`.

**Errors.** Everything in the loop is wrapped in `try/except Exception` and reported as `Error on line N: ...`. `SystemExit` (used by `exit` and by closing the canvas) passes through to the `finally` that calls `gui.shutdown()`.

## 4. wcsg.py

**Lifecycle.** `get_root()` creates one hidden `tk.Tk()`. Every window is a `Toplevel` of it. Nothing runs a normal `mainloop`: windows block with `wait_window` or `root.wait_variable(...)`, and animation uses `update()` and `root.after`. `shutdown()` restores the console, forgets the console and canvas and destroys the root.

**Window line grammar.**

```
line      := preset { "]" parameter [ value ] }
parameter := one of VALUE_PARAMS or FLAG_PARAMS
```

`split_outside_quotes(line, "]")` splits on `]` but not inside strings. `parse_line` returns `(preset, opts)`: it validates names, evaluates values with `eval(rest, variables)`, parses flags with `parse_flag`, and fills `opts` (defaults come from the preset: `size`, `resizable`, `anykey`).

**Showing a window.** `show_window` builds the `Toplevel`, draws the icon (`draw_icon` on a `Canvas`, or `load_icon` for `windowicon`), adds buttons by preset `kind` (`ok`, `yesno`, `okcancel`, `input`, `blank`) or custom `button`s, wires keys and dragging, places it with `place`, waits, and stores the result in `opts["save"]`.

**Console.** `console_open` makes the black `Text` window once. `console_print` appends a line and calls `update()`. `console_ask` adds an entry and a Done button and waits on an `IntVar`. `console_finish` waits for any key or click. The `release` callback in the state dict lets the close button end a pending wait.

**Canvas.** `canvas_open`, `canvas_clear`, `canvas_rect`, `canvas_circle`, `canvas_text`, `canvas_finish`. State lives in `_canvas` (`win`, `surface`, `keys`, `closed`, `wake`). `waitkey(ms)` clears `keys`, sleeps through `_wait` (which keeps the window alive) and returns the last key. A closed canvas raises `SystemExit` from `_need_canvas`.

**Terminal hiding.** `set_terminal_visible` calls `GetConsoleWindow` and `ShowWindow` through `ctypes`, inside `try/except`, so on other systems it does nothing.

## 5. Config and Modifier

`wc_modifier.py` imports `DEFAULTS` from `wc.py` and `PRESETS` / `POSITIONS` from `wcsg.py`.

- `COMMANDS`: `(config key, description, example)` per row of the settings table. `example` is formatted with `{kw}` for the current word. `None` hides the row from the help.
- `WORD_KEYS`: keys that must be one word, unique and not start with the comment symbol. `save()` validates them.
- `refresh_help()` builds the Help tab from the current config. Keep it in sync when you add commands.

## 6. Executable maker

`wc_exe_maker.py <folder>` checks for `start.wc`, copies the folder to `<name>_release`, adds `wc.py`, `wcsg.py`, `wc_config.json` if missing, then builds a tiny launcher with PyInstaller (`--onefile`, `--noconsole` on request, `icon.ico` if present). The launcher source is the `LAUNCHER` string. At run time it finds Python (`py -3`, `python`, then `python_windows.exe`), ignores the Microsoft Store stub (`WindowsApps`), runs `wc.py start.wc` in its own folder, and shows a message box if there is no Python. Flags: `--console`, `--noconsole`, `--no-build` (copy only, useful for testing).

## 7. Recipes

**A new command that users can rename**

1. `wc.py`: add `"pause": "pause"` to `DEFAULTS`.
2. `wc.py`: add a branch before the `canvas_words` branch:

```python
elif word == cfg["pause"]:
    input("Press Enter to continue...")
```

3. `wc_modifier.py`: add `("pause", "Wait for Enter", "{kw}")` to `COMMANDS` and `"pause"` to `WORD_KEYS`.
4. Add a row to the README keyword table.

**A new function for expressions.** Add it to the `variables` dict at the start of `run_program`:

```python
variables = {
    "year": datetime.now().year,
    "random": random.randint,
    "clamp": lambda value, low, high: max(low, min(high, value)),
}
```

**A new window preset.** Add an entry to `PRESETS` in `wcsg.py`. `kind` is `ok`, `yesno`, `okcancel`, `input` or `blank`; `icon` is a name known to `draw_icon` or `None`:

```python
"notice_window": {"icon": "info", "title": "Notice", "text": "", "kind": "ok",
                  "about": "info icon, OK button"},
```

**A new window parameter** (for example `padding 30`): add `"padding"` to `VALUE_PARAMS`, give `opts` a default in `parse_line`, parse it (`elif param == "padding": opts["padding"] = int(value)`), then use it in `show_window` (`body.pack(padx=opts["padding"], ...)`). Document it in the README table.

**A new canvas command** (for example `line`): write `canvas_line` in `wcsg.py`, then add `"line": "canvas_line"` to `canvas_words` in `wc.py`:

```python
def canvas_line(x1, y1, x2, y2, color="white", width=2):
    _need_canvas()["surface"].create_line(x1, y1, x2, y2, fill=color, width=width)
```

## 8. Testing

There is no test suite yet. Before every change:

1. Run all programs in `examples/` (`python wc.py examples/<name>/start.wc`).
2. Check error paths: a missing `end`, `end` without a block, `forcequit` outside a loop, a window line outside a zone.
3. For logic that does not need a screen, replace tkinter with a stub and the window function with a print. This runs on any machine:

```python
import sys, types
tk = types.ModuleType("tkinter"); tk.TclError = Exception
sys.modules["tkinter"] = tk
import wc, wcsg

wcsg.show_window = lambda preset, opts, variables, d, rv: print(preset["title"], opts["text"])
program = ['load standrt_gui', 'wcsgstart', 'Error_window ] speak ("hi")', 'wcsgstophere']
wc.run_program(program, wc.load_config(), ".")
```

4. Real windows can only be checked by running on Windows: look at every preset, the console, `force_noecho`, the canvas, and closing windows with the X button.

## 9. Conventions

- Messages for users are in English. Keep comments rare and short; prefer clear names.
- No new required dependencies. Optional ones (Pillow) must degrade gracefully.
- Keep modules importable: `main()` is guarded by `if __name__ == "__main__"`.
- Anything Windows-only goes through `try/except` so other systems keep working.
- A new keyword needs: `DEFAULTS`, the dispatch branch, the Modifier lists, the README table.

## 10. Release checklist

1. Run the examples and the error paths.
2. Update the version in both READMEs.
3. Build an `.exe` of a sample project with the maker and start it on a PC without Python (with and without `python_windows.exe`).
4. Create a GitHub Release (tag `v1.0`, `v1.1`...) and attach the ZIP and any `.exe` there.

## 11. Ideas

User-defined functions, `elif`, mouse input on the canvas, sounds, an "everything inside the .exe" mode where PyInstaller bundles the interpreter so Python is not needed, translating the Modifier interface to English.

## Note on spelling

The module name `standrt_gui` is a historical spelling that stays for compatibility. `standart_gui` is accepted as an alias.
