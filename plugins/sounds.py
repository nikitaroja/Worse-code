import ast
import ctypes
import itertools
import os


_mci_alias = None
_mci_ids = itertools.count(1)


def _mci(command):
    error = ctypes.windll.winmm.mciSendStringW(command, None, 0, None)
    if error:
        message = ctypes.create_unicode_buffer(256)
        ctypes.windll.winmm.mciGetErrorStringW(error, message, len(message))
        raise RuntimeError(message.value or f"MCI error {error}")


def _close_mci_alias(alias, stop=False):
    global _mci_alias
    try:
        if stop:
            _mci(f"stop {alias}")
    finally:
        try:
            _mci(f"close {alias}")
        finally:
            if _mci_alias == alias:
                _mci_alias = None


def play_file(path, wait=False):
    global _mci_alias

    if os.path.splitext(path)[1].lower() == ".wav":
        import winsound

        flags = winsound.SND_FILENAME
        if not wait:
            flags |= winsound.SND_ASYNC
        winsound.PlaySound(path, flags)
        return

    if _mci_alias is not None:
        _close_mci_alias(_mci_alias, stop=True)

    alias = f"wc_sound_{next(_mci_ids)}"
    _mci(f'open "{os.path.abspath(path)}" type mpegvideo alias {alias}')
    _mci_alias = alias
    try:
        _mci(f"play {alias}" + (" wait" if wait else ""))
    except Exception:
        _close_mci_alias(alias, stop=True)
        raise
    finally:
        if wait and _mci_alias == alias:
            _close_mci_alias(alias)


def stop_playback():
    if _mci_alias is not None:
        _mci(f"stop {_mci_alias}")
        return
    import winsound

    winsound.PlaySound(None, 0)


def register(wc):
    def play(ctx, rest):
        argument = rest.strip()
        if not argument:
            raise ValueError("use: play file.wav or file.mp3")

        if argument[0] in "\"'":
            try:
                sound = ast.literal_eval(argument)
            except (SyntaxError, ValueError) as error:
                raise ValueError("use: play file.wav or file.mp3") from error
            if not isinstance(sound, str) or not sound:
                raise ValueError("use: play file.wav or file.mp3")
        else:
            sound = argument

        drive, _ = os.path.splitdrive(sound)
        if drive or sound.startswith(("\\\\", "//")):
            path = sound
        else:
            path = os.path.join(ctx.program_dir, sound.lstrip("/\\"))

        if os.path.splitext(path)[1].lower() not in (".wav", ".mp3"):
            raise ValueError("Sounds supports .wav and .mp3 files only")
        if not os.path.isfile(path):
            raise ValueError(f"Sound file not found: {path}")

        try:
            if os.path.splitext(path)[1].lower() == ".wav":
                import winsound
            elif os.name != "nt":
                raise ImportError("MP3 playback uses Windows Media Control")
        except ImportError as error:
            raise ValueError("The Sounds plugin requires Windows") from error

        try:
            play_file(path)
        except RuntimeError as error:
            raise ValueError(f"Could not play sound: {error}") from error

    def sound_end(ctx, rest):
        if rest.strip():
            raise ValueError("use: sound_end")
        try:
            if "_mci_alias" in globals() and _mci_alias is not None:
                _close_mci_alias(_mci_alias, stop=True)
            else:
                stop_playback()
        except RuntimeError as error:
            raise ValueError(f"Could not stop sound: {error}") from error

    for key, default, handler in (
        ("play", "play", play),
        ("sound_end", "sound_end", sound_end),
    ):
        wc.command(key, default, handler)
