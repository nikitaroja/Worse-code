def register(wc):
    wc.command("shout", "shout", lambda ctx, rest: ctx.out(str(ctx.ev(rest)).upper()))
