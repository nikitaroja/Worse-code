# Worse Code (WC)

**A small programming language you can reshape to your taste.** Rename every keyword, open real windows, draw on a canvas and write games, all from plain text files and a single Python interpreter.

`Latest stable: Version 1b` · `In development: Version 2a` · Written in Python · Made on Windows · [Русская версия](README.ru.md)

![License: MIT](https://img.shields.io/badge/license-MIT-blue) ![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue) ![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey)

```
set name = "world"
say "Hello, " + name + "!"
```

## Contents

[Features](#features) · [Download](#download) · [Quick start](#quick-start) · [The language in five minutes](#the-language-in-five-minutes) · [Keywords](#keywords) · [Make the language yours](#make-the-language-yours) · [WCSG](#wcsg-windows-console-and-canvas) · [Plugins](#plugins) · [Examples](#examples) · [Build a .exe](#build-a-windows-exe) · [Roadmap](#roadmap)

## Features

- Simple readable syntax: variables, `if / else`, loops, lists, expressions.
- **Every keyword can be renamed**, in a small JSON file.
- **WCSG** (WC Standard GUI): ready-made windows (error, question, input, blank...), a black console window and the *MiniPaint* canvas with keyboard input.
- Real games are possible: a complete Snake in about 50 lines ([examples/snake](examples/snake)).
- **Executable maker**: drop a folder on a script and get a Windows `.exe`.
- **Plugins**: a plugin manager adds commands and functions to your project, with Standard, User and Hotfix categories.
- The interpreter is plain Python with no required third-party packages (Pillow is optional for `.jpg` icons, PyInstaller is only used by the executable maker).

## Download

- **Source code:** press the green **Code** button, choose **Download ZIP** and unpack it. This is the development version.
- **Releases:** open the **Releases** page. It has the stable versions and the **WC Basic Pack for Windows**, which comes with its own guide and demos.

### Version numbers

- A version is a number plus a letter: `Version 1a`, `Version 1b`, `Version 2a`. The number is the generation of the language, the letter is the release inside it. The newest release without the *Pre-release* mark is the stable one.
- A test build of the next version is named `<current>-<next>-devNN`, for example `Version 1b-2a-dev01`. It is published as a **Pre-release** (a *Developer Beta*) and may be unstable.
- Git tags follow the titles: `version-1b`, `version-1b-2a-dev01`.

## Quick start

**Requirements:** Python 3.8 or newer with tkinter (included in the official Windows installer). Windows is the main target.

```
git clone https://github.com/nikitaroja/Worse-Code.git
cd Worse-Code
python wc.py examples/hello/start.wc
```

Or download the ZIP from GitHub, unpack it and run the last command.

A program is a UTF-8 text file with the `.wc` extension:

```
python wc.py my_program.wc
```

Add `--pause` to keep the console open at the end. In Windows Notepad choose "All files" when saving, otherwise it saves `my_program.wc.txt`.

## The language in five minutes

The examples use the default keywords. You can change all of them (see [Make the language yours](#make-the-language-yours)).

**Output, variables, input**

```
set x = 5
set name = "Ann"
say "Hello, " + name
say x * 2
ask answer
```

`ask` reads a line: a number becomes a number, anything else stays text. Expressions are Python expressions, so `+ - * / ( )`, `str()`, `len()`, `range()` and friends work. The variable `year` holds the current year.

**Conditions** (`==  !=  <  >  <=  >=  and  or  not  in`)

```
if x > 3
    say "big"
else
    say "small"
end
```

Every block ends with `end`. There is no `elif` yet: put another `if` inside `else`.

**Loops**

```
set n = 0
makeuserdoright n < 3
    set n = n + 1
    say n
end

draw i in range(3)
    if i == 2
        forcequit
    end
    say i
end
```

`makeuserdoright` repeats while the condition is true, `draw x in list` walks through a list, `forcequit` leaves the innermost loop.

**Lists and random numbers**

```
set body = [[1, 1], [2, 1]]
make body.append([3, 1])
set body[0] = [9, 9]
set a, b = 1, 2
set dice = random(1, 6)
say len(body)
```

`make expression` evaluates an expression and ignores the result, which is how you call list methods.

**Other**

```
sleep 1.5
# a comment, also allowed after a command
exit
```

## Keywords

| Config key | Default word | Meaning |
|---|---|---|
| `say` | `say` | print a value |
| `set` | `set` | assign: `set x = 5`, `set a, b = 1, 2`, `set list[0] = 5` |
| `ask` | `ask` | read a number or text into a variable |
| `if` / `else` / `end` | `if` / `else` / `end` | conditions and the end of any block |
| `while` | `makeuserdoright` | loop while the condition is true |
| `for` | `draw` | loop over a list |
| `break` | `forcequit` | leave the innermost loop |
| `do` | `make` | evaluate an expression, ignore the result |
| `load` | `load` | load a module: `load standrt_gui` |
| `gui_start` / `gui_stop` | `wcsgstart` / `wcsgstophere` | begin / end a WCSG zone |
| `force_noecho` | `force_noecho` | hide the console for good, everything goes through WCSG |
| `canvas` | `minipaint` | open the canvas |
| `text` | `speaksymbols` | draw text on the canvas |
| `comment` | `#` | comment symbol |
| `prompt` | `> ` | prompt shown by `ask` |

Fixed words: `sleep`, `exit` / `quit`, `clear`, `rect`, `circle`, and the functions `random(a, b)` and `waitkey(ms)`.

## Make the language yours

Copy `wc_config.example.json` to `wc_config.json` and keep only the words you want to change:

```json
{
  "say": "speak",
  "set": "to",
  "ask": "whatnumber",
  "comment": "//"
}
```

Settings are layered: built-in defaults, then `wc_config.json` next to `wc.py`, then `wc_config.json` next to your program (so every project can have its own words). A command must be a single word, all commands must differ, and none may start with the comment symbol.

## WCSG: windows, console and canvas

```
load standrt_gui
wcsgstart
Error_window ] where center ] speak ("Test") ] fontspeak "Arial Black" ] windowicon "/error.png"
wcsgstophere
```

Load the module once with `load standrt_gui` (`standart_gui` also works). Window lines go between `wcsgstart` and `wcsgstophere` and look like `Preset ] parameter value ] parameter value`. Windows are modal: the program continues when the window is closed.

**Presets**

| Preset | What it is | Answer (with `save`) |
|---|---|---|
| `Error_window` | red cross, OK | |
| `Warning_window` | yellow triangle, OK | |
| `Info_window` | blue i, OK | |
| `Success_window` | green check, OK | |
| `Message_window` | plain text | |
| `Question_window` | Yes / No | `"yes"` or `"no"` |
| `Confirm_window` | OK / Cancel | `"ok"` or `"cancel"` |
| `Input_window` | text field | what was typed (a number if numeric) |
| `Blank_window` | large empty window, any key closes it | the key name, e.g. `"Return"` |

**Parameters**

| Parameter | Value | Meaning |
|---|---|---|
| `where` | `center` `left` `right` `top` `bottom` `topleft` `topright` `bottomleft` `bottomright` | position on the screen |
| `speak` | expression | window text |
| `title` | expression | title bar text |
| `fontspeak`, `fontsize` | `"Arial Black"`, `14` | font |
| `windowicon` | `"/error.png"` | picture next to the text, path relative to the program folder, scaled to about 56 px. PNG and GIF work out of the box, JPG needs Pillow |
| `bg`, `fg` | `"white"`, `"#202020"` | background and text colours |
| `size` | `"400x200"` | window size |
| `alpha` | `0.1` to `1` | transparency |
| `button` | `"Play"` | custom button, repeat it for several. Any button closes the window and its text goes to `save` |
| `save` | variable name | store the answer |

Flags (write them alone or with `yes` / `no`): `stndrt_icon_destroy` (remove the default feather icon from the title bar), `resizable`, `draggable` (drag by any point), `noborder`, `topmost` (on by default), `anykey` (any key closes the window).

```
Blank_window ] button "Play" ] button "Quit" ] save choice
```

**Console inside a zone.** Between `wcsgstart` and `wcsgstophere` the real console is hidden: `say` writes into a black *WC Console* window and `ask` shows an input field (Enter or the Done button). When the zone ends, a key press or click closes that window. `force_noecho` keeps the console hidden for the whole program. The console always comes back at the end or on an error. Hiding works in the classic Windows console; Windows Terminal may keep its window visible.

**Canvas.** Inside a zone:

```
minipaint 600, 400, "black"
clear
rect 10, 10, 100, 50, "green"
circle 300, 200, 30, "red"
speaksymbols 10, 360, "Score: 3", "white", 18
set key = waitkey(120)
```

`waitkey(ms)` waits for `ms` milliseconds and returns the last key pressed in that time (`"Up"`, `"Left"`, `"space"`, `"a"`...) or an empty string. It is the game tick. Closing the canvas window stops the program.

## Examples

| Folder | Shows |
|---|---|
| [examples/hello](examples/hello) | the smallest program |
| [examples/calculator](examples/calculator) | input and nested conditions |
| [examples/guess_number](examples/guess_number) | loops and `random` |
| [examples/windows_demo](examples/windows_demo) | WCSG windows and the black console |
| [examples/snake](examples/snake) | a full game on the canvas (arrow keys, Esc quits) |

Run any of them: `python wc.py examples/snake/start.wc`.

## Build a Windows .exe

*This tool is still in beta.*

1. Put your program in a folder with a `start.wc` file.
2. Drag the folder onto `wc_exe_maker.py`.
3. Take the `<folder>_release` folder it creates: it holds your files, the interpreter and the `.exe`.

The `.exe` looks for Python on the computer. If there is none and the program folder contains `python_windows.exe` (the official Python installer from python.org, renamed), it asks permission, installs Python silently for the current user (no administrator rights needed) and starts the program. Without an installer it shows "Python is required, but not installed". The maker installs PyInstaller once. Do not commit `.exe` files to git (the Python installer is also too big for the web uploader), attach them to a GitHub Release instead.

## Plugins

Plugins (a **developer beta**, planned for Version 2a) add commands and functions without editing the core. Run `python wc_plugin_manager.py`, choose your project folder and install what you need: **Standard** plugins (`pause`, `mathplus`, `beep`, `storage`), **User** plugins and **Hotfixes**. The manager edits your project's `wc_config.json` and, if needed, adds the plugin hooks to `wc.py`. How to write your own: [docs/PLUGINS.md](docs/PLUGINS.md).

## Safety

Plugins are Python code too, so install only plugins you trust.


WC evaluates expressions with Python's `eval` and `exec`. A `.wc` program can therefore do anything a Python script can. Only run programs you trust.

## Limitations

- No user-defined functions and no `elif` yet.
- `draw` takes one variable name.
- Console hiding and the executable maker target Windows.

## Roadmap

Ideas, not promises:

- user-defined functions and `elif`
- mouse input on the canvas and sounds
- an `.exe` that carries Python inside, so no installer is needed
- new plugins with every version

## Contributing

Ideas and pull requests are welcome. Read the [Developer Guide](docs/DEVELOPER_GUIDE.md) first, and the [plugin guide](docs/PLUGINS.md) if you want to write a plugin. Put your own programs into [projects](projects). Licensed under the MIT License.
