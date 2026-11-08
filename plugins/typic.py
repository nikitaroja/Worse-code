import sys
import time


CHAR_DELAY = 0.04


def write_terminal(value):
    sys.stdout.write(value)
    sys.stdout.flush()


def register(wc):
    def typic(ctx, rest):
        if not rest.strip():
            raise ValueError('use: typic "text"')

        text = str(ctx.ev(rest))
        write = getattr(ctx, "type_text", None) or write_terminal
        for character in text:
            write(character)
            time.sleep(CHAR_DELAY)
        write("\n")

    wc.command("typic", "typic", typic)
