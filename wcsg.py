"""WCSG: WC Standard GUI."""
import os
import tkinter as tk

PRESETS = {
    "error_window":    {"icon": "error",    "title": "Error",         "text": "An error occurred",  "kind": "ok",
                        "about": "red cross, OK button"},
    "warning_window":  {"icon": "warning",  "title": "Warning",       "text": "Warning!",           "kind": "ok",
                        "about": "yellow triangle, OK button"},
    "info_window":     {"icon": "info",     "title": "Information",   "text": "Message",            "kind": "ok",
                        "about": "blue letter i, OK button"},
    "success_window":  {"icon": "success",  "title": "Success",       "text": "Done!",              "kind": "ok",
                        "about": "green check mark, OK button"},
    "message_window":  {"icon": None,       "title": "Message",       "text": "",                   "kind": "ok",
                        "about": "plain text, no icon"},
    "question_window": {"icon": "question", "title": "Question",      "text": "Are you sure?",      "kind": "yesno",
                        "about": "Yes/No, answer is yes or no (save)"},
    "confirm_window":  {"icon": "question", "title": "Confirm",       "text": "Continue?",          "kind": "okcancel",
                        "about": "OK/Cancel, answer is ok or cancel (save)"},
    "input_window":    {"icon": "input",    "title": "Input",         "text": "Enter a value:",     "kind": "input",
                        "about": "input field, the answer goes to save"},
    "blank_window":    {"icon": None,       "title": "Blank",         "text": "",                   "kind": "blank",
                        "about": "large empty window, any key closes it (key name goes to save)",
                        "size": (900, 600), "resizable": True, "anykey": True},
}

POSITIONS = {
    "center": ("center", "center"), "left": ("center", "left"), "right": ("center", "right"),
    "top": ("top", "center"), "bottom": ("bottom", "center"),
    "topleft": ("top", "left"), "topright": ("top", "right"),
    "bottomleft": ("bottom", "left"), "bottomright": ("bottom", "right"),
}

VALUE_PARAMS = ("where", "speak", "title", "fontspeak", "fontsize", "windowicon",
                "bg", "fg", "save", "size", "alpha", "button")
FLAG_PARAMS = ("stndrt_icon_destroy", "resizable", "draggable", "noborder", "topmost", "anykey")
PARAMS = VALUE_PARAMS + FLAG_PARAMS

_root = None
_console = None
_canvas = None


def get_root():
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root


def shutdown():
    global _root, _console, _canvas
    set_terminal_visible(True)
    _console = None
    _canvas = None
    if _root is not None:
        try:
            _root.destroy()
        except tk.TclError:
            pass
        _root = None


def split_outside_quotes(text, sep):
    parts, current, quote, i = [], "", None, 0
    while i < len(text):
        ch = text[i]
        if quote:
            current += ch
            if ch == "\\" and i + 1 < len(text):
                i += 1
                current += text[i]
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            current += ch
        elif ch == sep:
            parts.append(current)
            current = ""
        else:
            current += ch
        i += 1
    parts.append(current)
    return parts


def split_word(text):
    i = 0
    while i < len(text) and (text[i].isalnum() or text[i] == "_"):
        i += 1
    return text[:i], text[i:]


def as_text(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def parse_flag(param, rest):
    if not rest:
        return True
    value = rest.strip("()\"' ").lower()
    if value in ("yes", "true", "on", "1"):
        return True
    if value in ("no", "false", "off", "0"):
        return False
    raise ValueError(f"Parameter '{param}' expects yes or no")


def parse_line(line, variables):
    parts = split_outside_quotes(line, "]")
    name = parts[0].strip()
    if name.lower() not in PRESETS:
        raise ValueError(f"Unknown window '{name}'. Available: " + ", ".join(PRESETS))
    preset = PRESETS[name.lower()]
    opts = {"where": "center", "text": preset["text"], "title": preset["title"],
            "font": "Segoe UI", "font_size": 11, "icon_path": None,
            "bg": "#f0f0f0", "fg": "black", "save": None,
            "window_size": preset.get("size"), "alpha": 1.0, "icon_destroy": False,
            "resizable": preset.get("resizable", False), "draggable": None, "noborder": False,
            "topmost": True, "anykey": preset.get("anykey", False), "buttons": []}

    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        word, rest = split_word(part)
        param, rest = word.lower(), rest.strip()
        if param not in PARAMS:
            raise ValueError(f"Unknown WCSG parameter '{word}'. Available: " + ", ".join(PARAMS))

        if param in FLAG_PARAMS:
            key = "icon_destroy" if param == "stndrt_icon_destroy" else param
            opts[key] = parse_flag(param, rest)
            continue
        if not rest:
            raise ValueError(f"Parameter '{word}' has no value")

        if param == "where":
            value = rest.strip("()\"' ").lower()
            if value not in POSITIONS:
                raise ValueError(f"Unknown position '{value}'. Available: " + ", ".join(POSITIONS))
            opts["where"] = value
        elif param == "save":
            opts["save"] = rest
        else:
            value = eval(rest, variables)
            if param == "speak":
                opts["text"] = as_text(value)
            elif param == "title":
                opts["title"] = as_text(value)
            elif param == "fontspeak":
                opts["font"] = str(value)
            elif param == "fontsize":
                opts["font_size"] = int(value)
            elif param == "windowicon":
                opts["icon_path"] = str(value)
            elif param == "bg":
                opts["bg"] = str(value)
            elif param == "fg":
                opts["fg"] = str(value)
            elif param == "size":
                try:
                    width, height = (int(x) for x in str(value).lower().split("x"))
                except ValueError:
                    raise ValueError("size must look like 400x200")
                opts["window_size"] = (width, height)
            elif param == "alpha":
                alpha = float(value)
                if not 0.1 <= alpha <= 1:
                    raise ValueError("alpha must be between 0.1 and 1")
                opts["alpha"] = alpha
            elif param == "button":
                opts["buttons"].append(as_text(value))
    return preset, opts


def draw_icon(c, kind):
    if kind == "error":
        c.create_oval(4, 4, 52, 52, fill="#d93025", outline="")
        c.create_line(19, 19, 37, 37, fill="white", width=5, capstyle="round")
        c.create_line(37, 19, 19, 37, fill="white", width=5, capstyle="round")
    elif kind == "warning":
        c.create_polygon(28, 5, 53, 49, 3, 49, fill="#f9ab00", outline="")
        c.create_text(28, 34, text="!", fill="white", font=("Segoe UI", 22, "bold"))
    elif kind == "success":
        c.create_oval(4, 4, 52, 52, fill="#188038", outline="")
        c.create_line(16, 29, 25, 38, 41, 19, fill="white", width=5, capstyle="round", joinstyle="round")
    else:
        color, symbol = {"info": ("#1a73e8", "i"), "question": ("#1a73e8", "?"), "input": ("#5f6368", "A")}[kind]
        c.create_oval(4, 4, 52, 52, fill=color, outline="")
        c.create_text(28, 28, text=symbol, fill="white", font=("Segoe UI", 24, "bold"))


def fit_image(img, size=56):
    big = max(img.width(), img.height())
    if big <= size:
        return img
    coarse = big // (size * 2)
    if coarse > 1:
        img = img.subsample(coarse)
        big = max(img.width(), img.height())
    best = (1, -(-big // size))
    for n in range(1, 5):
        for d in range(n, 17):
            if n * big <= size * d and n * best[1] > best[0] * d:
                best = (n, d)
    n, d = best
    if n > 1:
        img = img.zoom(n)
    return img.subsample(d) if d > 1 else img


def load_icon(path, program_dir, master):
    full = path if os.path.splitdrive(path)[0] else os.path.join(program_dir, path.lstrip("/\\"))
    if not os.path.exists(full):
        print(f"WCSG: icon not found: {full}")
        return None
    try:
        from PIL import Image, ImageTk
    except ImportError:
        Image = None
    if Image is not None:
        try:
            img = Image.open(full)
            img.thumbnail((56, 56))
            return ImageTk.PhotoImage(img, master=master)
        except Exception as error:
            print(f"WCSG: cannot open icon: {error}")
            return None
    try:
        img = tk.PhotoImage(file=full, master=master)
    except tk.TclError:
        print("WCSG: .jpg needs Pillow (pip install pillow). png and gif work without it.")
        return None
    return fit_image(img)


def place(win, where, size=None):
    win.update_idletasks()
    w, h = size if size else (win.winfo_reqwidth(), win.winfo_reqheight())
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    margin = 40
    vert, horiz = POSITIONS[where]
    x = {"left": margin, "center": (sw - w) // 2, "right": sw - w - margin}[horiz]
    y = {"top": margin, "center": (sh - h) // 2, "bottom": sh - h - margin - 40}[vert]
    win.geometry(f"{w}x{h}+{x}+{y}" if size else f"+{x}+{y}")


def show_window(preset, opts, variables, program_dir, read_value):
    root = get_root()
    bg, fg = opts["bg"], opts["fg"]
    font = (opts["font"], opts["font_size"])
    kind = preset["kind"]
    draggable = opts["draggable"] if opts["draggable"] is not None else opts["noborder"]

    win = tk.Toplevel(root)
    win.title(opts["title"])
    win.configure(bg=bg)
    win.resizable(opts["resizable"], opts["resizable"])
    win.attributes("-topmost", opts["topmost"])
    win.attributes("-alpha", opts["alpha"])
    if opts["icon_destroy"]:
        blank = tk.PhotoImage(width=1, height=1)
        win.iconphoto(False, blank)
        win._blank_icon = blank
    if opts["noborder"]:
        win.overrideredirect(True)

    body = tk.Frame(win, bg=bg)
    body.pack(padx=22, pady=(22, 12), fill="both", expand=True)

    image = load_icon(opts["icon_path"], program_dir, root) if opts["icon_path"] else None
    if image is not None:
        tk.Label(body, image=image, bg=bg).pack(side="left", padx=(0, 16))
    elif preset["icon"]:
        canvas = tk.Canvas(body, width=56, height=56, bg=bg, highlightthickness=0)
        draw_icon(canvas, preset["icon"])
        canvas.pack(side="left", padx=(0, 16))
    label = tk.Label(body, text=opts["text"], bg=bg, fg=fg, font=font, justify="left", wraplength=360)
    label.pack(side="left")

    entry = None
    if kind == "input":
        entry = tk.Entry(win, font=font, width=34)
        entry.pack(padx=22, pady=(0, 12), fill="x")

    result = {"value": None}

    def close(value):
        result["value"] = value
        win.destroy()

    buttons = tk.Frame(win, bg=bg)
    custom = bool(opts["buttons"]) and kind != "input"
    if custom or kind != "blank":
        buttons.pack(pady=(0, 18))

    def add_button(text, command):
        tk.Button(buttons, text=text, width=max(10, len(text) + 2), command=command).pack(side="left", padx=6)

    if custom:
        closing = ""
        for caption in opts["buttons"]:
            add_button(caption, lambda value=caption: close(value))
    elif kind == "ok":
        closing = "ok"
        add_button("OK", lambda: close("ok"))
    elif kind == "yesno":
        closing = "no"
        add_button("Yes", lambda: close("yes"))
        add_button("No", lambda: close("no"))
    elif kind == "okcancel":
        closing = "cancel"
        add_button("OK", lambda: close("ok"))
        add_button("Cancel", lambda: close("cancel"))
    elif kind == "blank":
        closing = ""
    else:
        closing = ""
        add_button("OK", lambda: close(entry.get()))
        add_button("Cancel", lambda: close(""))

    win.protocol("WM_DELETE_WINDOW", lambda: close(closing))
    if opts["anykey"] and kind != "input":
        win.bind("<Key>", lambda e: close(e.keysym))
    else:
        win.bind("<Escape>", lambda e: close(closing))
        win.bind("<Return>", lambda e: close(entry.get() if entry else "ok" if kind == "ok" else closing))

    if draggable:
        drag = {"on": False, "x": 0, "y": 0}

        def start_drag(event):
            if isinstance(event.widget, (tk.Entry, tk.Button)):
                drag["on"] = False
                return
            drag.update(on=True, x=event.x_root - win.winfo_x(), y=event.y_root - win.winfo_y())

        def do_drag(event):
            if drag["on"]:
                win.geometry(f"+{event.x_root - drag['x']}+{event.y_root - drag['y']}")

        win.bind("<ButtonPress-1>", start_drag)
        win.bind("<B1-Motion>", do_drag)

    if opts["resizable"]:
        win.update_idletasks()
        win.minsize(win.winfo_reqwidth(), win.winfo_reqheight())

        def rewrap(event):
            if event.widget is win:
                label.config(wraplength=max(100, event.width - 140))

        win.bind("<Configure>", rewrap)

    place(win, opts["where"], opts["window_size"])
    win.focus_force()
    if entry:
        entry.focus_set()
    win.wait_window()

    value = result["value"] if result["value"] is not None else closing
    if opts["save"]:
        variables[opts["save"]] = read_value(value) if kind == "input" else value


def run_line(line, variables, program_dir, read_value):
    preset, opts = parse_line(line, variables)
    show_window(preset, opts, variables, program_dir, read_value)


def set_terminal_visible(visible):
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5 if visible else 0)
    except Exception:
        pass


def _console_x():
    c = _console
    if c is None:
        return
    if c["release"] is not None:
        c["release"]("")
    else:
        c["win"].destroy()


def console_open():
    global _console
    if _console is not None and _console["win"].winfo_exists():
        return _console
    win = tk.Toplevel(get_root())
    win.title("WC Console")
    win.configure(bg="black")
    bar = tk.Frame(win, bg="black")
    bar.pack(side="bottom", fill="x")
    text = tk.Text(win, bg="black", fg="#cccccc", font=("Consolas", 11), wrap="word",
                   state="disabled", borderwidth=0, highlightthickness=0, padx=10, pady=8)
    text.pack(side="top", fill="both", expand=True)
    _console = {"win": win, "text": text, "bar": bar, "release": None}
    win.protocol("WM_DELETE_WINDOW", _console_x)
    place(win, "center", (720, 420))
    return _console


def console_print(value):
    c = console_open()
    text = c["text"]
    text.configure(state="normal")
    text.insert("end", as_text(value) + "\n")
    text.see("end")
    text.configure(state="disabled")
    c["win"].update()


def console_ask(prompt):
    c = console_open()
    root = get_root()
    row = tk.Frame(c["bar"], bg="black")
    row.pack(fill="x", padx=8, pady=6)
    tk.Label(row, text=prompt, bg="black", fg="#33ff66", font=("Consolas", 11)).pack(side="left")
    done = tk.IntVar(master=root)
    answer = {"value": ""}

    def release(value):
        answer["value"] = value
        done.set(1)

    c["release"] = release
    tk.Button(row, text="Done", command=lambda: release(entry.get())).pack(side="right")
    entry = tk.Entry(row, bg="#111111", fg="#33ff66", insertbackground="#33ff66",
                     font=("Consolas", 11), relief="flat")
    entry.pack(side="left", fill="x", expand=True, padx=6)
    entry.bind("<Return>", lambda e: release(entry.get()))
    c["win"].focus_force()
    entry.focus_set()
    root.wait_variable(done)
    c["release"] = None
    if c["win"].winfo_exists():
        row.destroy()
        console_print(prompt + answer["value"])
    return answer["value"]


def console_finish():
    c = _console
    if c is None or not c["win"].winfo_exists():
        return
    console_print("[ press any key to close ]")
    root = get_root()
    done = tk.IntVar(master=root)
    c["release"] = lambda value: done.set(1)
    c["win"].bind("<Key>", lambda e: done.set(1))
    c["win"].bind("<ButtonPress>", lambda e: done.set(1))
    c["win"].focus_force()
    root.wait_variable(done)
    c["release"] = None
    c["win"].destroy()


def has_windows():
    return any(w is not None and w["win"].winfo_exists() for w in (_console, _canvas))


def _need_canvas():
    if _canvas is None:
        raise ValueError("No MiniPaint window is open")
    if _canvas["closed"]:
        raise SystemExit
    return _canvas


def canvas_open(width, height, bg="black"):
    global _canvas
    if _canvas is not None and _canvas["win"].winfo_exists():
        _canvas["win"].destroy()
    width, height = int(width), int(height)
    win = tk.Toplevel(get_root())
    win.title("MiniPaint")
    win.resizable(False, False)
    surface = tk.Canvas(win, width=width, height=height, bg=str(bg), highlightthickness=0)
    surface.pack()
    state = {"win": win, "surface": surface, "keys": [], "closed": False, "wake": None}

    def on_close():
        state["closed"] = True
        if state["wake"]:
            state["wake"]()
        win.destroy()

    win.bind("<Key>", lambda e: state["keys"].append(e.keysym))
    win.protocol("WM_DELETE_WINDOW", on_close)
    _canvas = state
    place(win, "center", (width, height))
    win.focus_force()
    win.update()


def canvas_clear():
    _need_canvas()["surface"].delete("all")


def canvas_rect(x, y, w, h, color="white"):
    _need_canvas()["surface"].create_rectangle(x, y, x + w, y + h, fill=color, outline="")


def canvas_circle(x, y, r, color="white"):
    _need_canvas()["surface"].create_oval(x - r, y - r, x + r, y + r, fill=color, outline="")


def canvas_text(x, y, text, color="white", size=14):
    _need_canvas()["surface"].create_text(
        x, y, text=as_text(text), fill=color, anchor="nw", font=("Consolas", int(size), "bold"))


def _wait(ms, state=None):
    root = get_root()
    done = tk.IntVar(master=root)
    if state is not None:
        state["wake"] = lambda: done.set(1)
    root.after(max(1, int(ms)), lambda: done.set(1))
    root.wait_variable(done)
    if state is not None:
        state["wake"] = None


def waitkey(ms=0):
    c = _need_canvas()
    c["keys"] = []
    _wait(ms, c)
    if c["closed"]:
        raise SystemExit
    return c["keys"][-1] if c["keys"] else ""


def sleep(seconds):
    state = _canvas if _canvas is not None and not _canvas["closed"] else None
    _wait(float(seconds) * 1000, state)
    if _canvas is not None and _canvas["closed"]:
        raise SystemExit


def canvas_finish():
    global _canvas
    c = _canvas
    if c is None or c["closed"] or not c["win"].winfo_exists():
        _canvas = None
        return
    surface = c["surface"]
    surface.create_text(int(surface.cget("width")) // 2, int(surface.cget("height")) - 14,
                        text="[ press any key to close ]", fill="#888888", font=("Consolas", 10))
    c["win"].update()
    root = get_root()
    done = tk.IntVar(master=root)
    c["wake"] = lambda: done.set(1)
    c["win"].bind("<Key>", lambda e: done.set(1))
    c["win"].bind("<ButtonPress>", lambda e: done.set(1))
    c["win"].focus_force()
    root.wait_variable(done)
    if c["win"].winfo_exists():
        c["win"].destroy()
    _canvas = None
