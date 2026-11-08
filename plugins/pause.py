def register(wc):
    def run(ctx, rest):
        ctx.ask(str(ctx.ev(rest)) if rest.strip() else "Press Enter to continue...")

    wc.command("pause", "pause", run)
