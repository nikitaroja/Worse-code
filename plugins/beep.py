def register(wc):
    def run(ctx, rest):
        values = ctx.ev("(" + rest + ",)") if rest.strip() else ()
        frequency = values[0] if len(values) > 0 else 750
        duration = values[1] if len(values) > 1 else 150
        try:
            import winsound
            winsound.Beep(int(frequency), int(duration))
        except Exception:
            print("\a", end="")

    wc.command("beep", "beep", run)
