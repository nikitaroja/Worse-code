import json
import os


def register(wc):
    def path():
        return os.path.join(wc.ctx.program_dir, "storage.json")

    def read_all():
        try:
            with open(path(), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def store(ctx, rest):
        key, separator, value = rest.partition("=")
        if not separator or not key.strip():
            raise ValueError("use: store name = value")
        data = read_all()
        data[key.strip()] = ctx.ev(value)
        with open(path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    wc.command("store", "store", store)
    wc.function("recall", lambda key, default=None: read_all().get(key, default))
