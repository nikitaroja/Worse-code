def register(wc):
    wc.function("clamp", lambda value, low, high: max(low, min(high, value)))
    wc.function("sign", lambda value: (value > 0) - (value < 0))
    wc.function("avg", lambda items: sum(items) / len(items))
