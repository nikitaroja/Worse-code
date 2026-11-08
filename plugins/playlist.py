import ast
import ctypes
import os
import threading
import time


KEY_CODES = {
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "SPACE": 0x20,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "TAB": 0x09,
    "BACKSPACE": 0x08,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
}


def parse_string(value, description):
    try:
        result = ast.literal_eval(value.strip())
    except (SyntaxError, ValueError) as error:
        raise ValueError(f"{description} must be a quoted string") from error
    if not isinstance(result, str) or not result:
        raise ValueError(f"{description} must be a non-empty quoted string")
    return result


def resolve_path(program_dir, sound):
    drive, _ = os.path.splitdrive(sound)
    if drive or sound.startswith(("\\\\", "//")):
        path = sound
    else:
        path = os.path.join(program_dir, sound.lstrip("/\\"))
    if os.path.splitext(path)[1].lower() not in (".wav", ".mp3"):
        raise ValueError("Playlist supports .wav and .mp3 files only")
    if not os.path.isfile(path):
        raise ValueError(f"Sound file not found: {path}")
    return path


def key_code(name):
    name = name.strip().upper()
    if name in KEY_CODES:
        return KEY_CODES[name]
    if len(name) == 1 and name.isascii() and name.isalnum():
        return ord(name)
    raise ValueError(f"Unsupported key '{name}'. Use ENTER, SPACE, ESC, arrows, or one letter/digit")


def key_is_down(code):
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(code) & 0x8000)
    except AttributeError as error:
        raise ValueError("Keyboard-controlled playlists require Windows") from error


def play_track(sound, path, interrupt_key):
    errors = []

    def play():
        try:
            sound.play_file(path, wait=True)
        except Exception as error:
            errors.append(error)

    was_down = key_is_down(interrupt_key) if interrupt_key is not None else False
    worker = threading.Thread(target=play, daemon=True)
    worker.start()

    while worker.is_alive():
        if interrupt_key is not None:
            down = key_is_down(interrupt_key)
            if down and not was_down:
                sound.stop_playback()
                worker.join()
                if errors:
                    raise ValueError(f"Could not play sound: {errors[0]}") from errors[0]
                return True
            was_down = down
        time.sleep(0.02)

    worker.join()
    if errors:
        raise ValueError(f"Could not play sound: {errors[0]}") from errors[0]
    return False


def register(wc):
    tracks = []
    blocklast = False
    started = False

    def playlist(ctx, rest):
        nonlocal blocklast, started
        if rest.strip():
            raise ValueError("use: playlist")
        tracks.clear()
        blocklast = False
        started = True

    def track(ctx, rest):
        if not started:
            raise ValueError("start a playlist before adding tracks")
        label, separator, sound = rest.partition("=")
        if not separator:
            raise ValueError('use: track "1" = "1.wav"')
        label = parse_string(label, "Track name")
        path = parse_string(sound, "Track file")
        if any(existing_label == label for existing_label, _ in tracks):
            raise ValueError(f"Track '{label}' is already in this playlist")
        tracks.append((label, path))

    def set_blocklast(ctx, rest):
        nonlocal blocklast
        if not started:
            raise ValueError("start a playlist before setting blocklast")
        _, separator, value = rest.partition("=")
        if not separator:
            raise ValueError("use: blocklast = true or blocklast = false")
        value = value.strip().lower()
        if value not in ("true", "false"):
            raise ValueError("blocklast must be true or false")
        blocklast = value == "true"

    def changenow(ctx, rest):
        if not started:
            raise ValueError("start a playlist before changenow")
        if not tracks:
            raise ValueError("add at least one track before changenow")

        mode, _, key = rest.strip().partition(" ")
        mode = mode.lower()
        if mode not in ("block", "key"):
            raise ValueError('use: changenow:block or changenow:key "ENTER"')
        interrupt_key = key_code(parse_string(key, "Key")) if mode == "key" else None
        sound = wc.plugin("sounds")
        paths = [resolve_path(ctx.program_dir, path) for _, path in tracks]
        index = 0

        while True:
            play_track(sound, paths[index], interrupt_key)
            index += 1

            if index == len(paths):
                if blocklast:
                    return
                index = 0

    wc.command("playlist", "playlist", playlist)
    wc.command("track", "track", track)
    wc.command("blocklast", "blocklast", set_blocklast)
    wc.command("changenow", "changenow", changenow)
