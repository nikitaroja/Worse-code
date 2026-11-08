import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.join(HERE, "plugins")
LIST_FILE = os.path.join(HERE, "plugins.txt")
CATEGORIES = ("standard", "user", "hotfix")
TITLES = {"standard": "Standard", "user": "User", "hotfix": "Hotfixes"}
FIXED_WORDS = ("sleep", "exit", "quit", "clear", "rect", "circle")

CORE_HOOKS = [
    {
        "marker": "import wc_plugins",
        "anchor": "from datetime import datetime\n",
        "where": "after",
        "text": "try:\n    import wc_plugins\nexcept ImportError:\n    wc_plugins = None\n",
    },
    {
        "marker": "wc_plugins.load(",
        "anchor": "    program = []\n    for number, raw in enumerate(lines, start=1):\n",
        "where": "before",
        "text": (
            "    def ask_text(prompt):\n"
            "        return gui.console_ask(prompt) if use_gui_console() else input(prompt)\n\n"
            "    plugin = wc_plugins.load(cfg, program_dir, variables, ev, out, ask_text) if wc_plugins else None\n\n"
        ),
    },
    {
        "marker": "plugin.handles(",
        "anchor": "                elif in_gui:\n                    gui.run_line(line, variables, program_dir, read_value)\n",
        "where": "before",
        "text": "                elif plugin is not None and plugin.handles(word):\n                    plugin.run(word, rest)\n",
    },
]


class ManagerError(Exception):
    pass


class CoreError(ManagerError):
    pass


class ConflictError(ManagerError):
    def __init__(self, conflicts):
        super().__init__("; ".join(f"'{word}' ({key}) is already used by {owner}" for key, word, owner in conflicts))
        self.conflicts = conflicts


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def same_path(a, b):
    return os.path.abspath(a) == os.path.abspath(b)


def backup(path, tag):
    target = f"{path}.bak_{tag}"
    if not os.path.exists(target):
        shutil.copy2(path, target)


def valid_word(word):
    return isinstance(word, str) and word.isidentifier()


def read_list():
    result = {category: [] for category in CATEGORIES}
    try:
        lines = read_text(LIST_FILE).splitlines()
    except FileNotFoundError:
        return result
    section = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            name = line[1:-1].strip().lower()
            section = name if name in result else None
        elif section and line not in result[section]:
            result[section].append(line)
    return result


def write_list(data):
    lines = ["# Worse Code plugin list.",
             "# One plugin id per line. Details are in plugins/<id>.json, code in plugins/<id>.py.", ""]
    for category in CATEGORIES:
        lines.append(f"[{category}]")
        lines += data[category]
        lines.append("")
    write_text(LIST_FILE, "\n".join(lines))


def read_info(plugin_id, category):
    path = os.path.join(CATALOG_DIR, plugin_id + ".json")
    try:
        info = json.loads(read_text(path))
    except FileNotFoundError:
        raise ManagerError(f"plugins/{plugin_id}.json is missing")
    except json.JSONDecodeError as error:
        raise ManagerError(f"plugins/{plugin_id}.json is not valid JSON: {error}")
    info["id"] = plugin_id
    info["category"] = category
    for key, default in (("name", plugin_id), ("version", "1.0"), ("author", ""), ("description", ""),
                         ("commands", {}), ("functions", []), ("depends", []), ("example", "")):
        info.setdefault(key, default)
    if category == "hotfix":
        info.setdefault("patches", [])
    else:
        info.setdefault("file", plugin_id + ".py")
    return info


def find_info(plugin_id):
    for category, ids in read_list().items():
        if plugin_id in ids:
            return read_info(plugin_id, category)
    raise ManagerError(f"Unknown plugin '{plugin_id}'. Add it to plugins.txt first.")


def catalog():
    items = []
    for category, ids in read_list().items():
        for plugin_id in ids:
            try:
                items.append(read_info(plugin_id, category))
            except ManagerError as error:
                items.append({"id": plugin_id, "name": plugin_id, "category": category, "version": "?",
                              "description": f"Broken plugin: {error}", "commands": {}, "functions": [],
                              "depends": [], "author": "", "example": "", "broken": True})
    return items


def check_project(project):
    if not project or not os.path.isdir(project):
        raise ManagerError("Choose the project folder first")


def config_path(project):
    return os.path.join(project, "wc_config.json")


def read_config(project):
    try:
        return json.loads(read_text(config_path(project)))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        raise ManagerError(f"{config_path(project)} is not valid JSON: {error}")


def write_config(project, cfg):
    write_text(config_path(project), json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")


def core_path(project):
    own = os.path.join(project, "wc.py")
    return own if os.path.exists(own) else os.path.join(HERE, "wc.py")


def support_state(project):
    path = core_path(project)
    text = read_text(path)
    missing = [hook["marker"] for hook in CORE_HOOKS if hook["marker"] not in text]
    return path, not missing


def enable_support(project, replace=False):
    path = core_path(project)
    core_dir = os.path.dirname(path)
    notes = []
    latest = os.path.join(HERE, "wc.py")
    if replace and not same_path(latest, path):
        backup(path, "before_plugins")
        shutil.copy2(latest, path)
        notes.append(f"Replaced {path} with the latest wc.py (backup: wc.py.bak_before_plugins)")
    text = read_text(path)
    new_text = text
    for hook in CORE_HOOKS:
        if hook["marker"] in new_text:
            continue
        if new_text.count(hook["anchor"]) != 1:
            raise CoreError(f"{path} was customized and the plugin hooks do not fit")
        joined = hook["anchor"] + hook["text"] if hook["where"] == "after" else hook["text"] + hook["anchor"]
        new_text = new_text.replace(hook["anchor"], joined)
    if new_text != text:
        backup(path, "before_plugins")
        write_text(path, new_text)
        notes.append(f"Added plugin hooks to {path}")
    source = os.path.join(HERE, "wc_plugins.py")
    target = os.path.join(core_dir, "wc_plugins.py")
    if not same_path(source, target) and (not os.path.exists(target) or read_text(target) != read_text(source)):
        shutil.copy2(source, target)
        notes.append(f"Copied wc_plugins.py to {core_dir}")
    return notes


def taken_words(project, ignore=None):
    sys.path.insert(0, HERE)
    from wc import DEFAULTS
    cfg = read_config(project)
    words = {}
    for key, default in DEFAULTS.items():
        if key not in ("comment", "prompt"):
            words[cfg.get(key, default)] = f"the core keyword '{key}'"
    for word in FIXED_WORDS:
        words[word] = "a built-in word"
    for plugin_id in cfg.get("plugins", []):
        if plugin_id == ignore:
            continue
        try:
            commands = find_info(plugin_id)["commands"]
        except ManagerError:
            continue
        for key, default in commands.items():
            words[cfg.get(key, default)] = f"the plugin '{plugin_id}'"
    return words


def install(project, plugin_id, renames=None, _stack=()):
    check_project(project)
    info = find_info(plugin_id)
    if info["category"] == "hotfix":
        return apply_hotfix(project, info)
    notes = enable_support(project)
    cfg = read_config(project)
    for dependency in info["depends"]:
        if dependency in cfg.get("plugins", []):
            continue
        if dependency in _stack or dependency == plugin_id:
            raise ManagerError("Circular plugin dependency")
        notes += install(project, dependency, None, _stack + (plugin_id,))
        cfg = read_config(project)
    source = os.path.join(CATALOG_DIR, info["file"])
    if not os.path.exists(source):
        raise ManagerError(f"plugins/{info['file']} is missing")

    renames = renames or {}
    words = {key: renames.get(key) or cfg.get(key) or default for key, default in info["commands"].items()}
    for word in words.values():
        if not valid_word(word):
            raise ManagerError(f"'{word}' cannot be a keyword: use letters, digits and underscores")
    if len(set(words.values())) < len(words):
        raise ManagerError("Two commands of this plugin would share one word")
    taken = taken_words(project, ignore=plugin_id)
    problems = [(key, word, taken[word]) for key, word in words.items() if word in taken]
    if problems:
        raise ConflictError(problems)

    target_dir = os.path.join(project, "plugins")
    if not same_path(target_dir, CATALOG_DIR):
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(source, os.path.join(target_dir, info["file"]))
    plugins = cfg.setdefault("plugins", [])
    if plugin_id not in plugins:
        plugins.append(plugin_id)
    cfg.update(words)
    write_config(project, cfg)
    notes.append(f"Installed '{plugin_id}' into {project}")
    return notes


def remove(project, plugin_id):
    check_project(project)
    info = find_info(plugin_id)
    if info["category"] == "hotfix":
        return apply_hotfix(project, info, reverse=True)
    cfg = read_config(project)
    plugins = cfg.get("plugins", [])
    if plugin_id not in plugins:
        raise ManagerError(f"'{plugin_id}' is not installed in this project")
    for other in plugins:
        if other == plugin_id:
            continue
        try:
            needs = find_info(other)["depends"]
        except ManagerError:
            continue
        if plugin_id in needs:
            raise ManagerError(f"'{other}' needs '{plugin_id}', remove it first")
    plugins.remove(plugin_id)
    for key in info["commands"]:
        cfg.pop(key, None)
    target_dir = os.path.join(project, "plugins")
    path = os.path.join(target_dir, info["file"])
    if not same_path(target_dir, CATALOG_DIR) and os.path.exists(path):
        os.remove(path)
    write_config(project, cfg)
    return [f"Removed '{plugin_id}' from {project}"]


def patch_states(project, info):
    core_dir = os.path.dirname(core_path(project))
    states = []
    for patch in info["patches"]:
        try:
            text = read_text(os.path.join(core_dir, patch["file"]))
        except FileNotFoundError:
            states.append("missing")
            continue
        if patch["find"] in text:
            states.append("pending")
        elif patch["replace"] in text:
            states.append("applied")
        else:
            states.append("conflict")
    return states


def hotfix_applied(project, info):
    states = patch_states(project, info)
    return bool(states) and all(state == "applied" for state in states)


def apply_hotfix(project, info, reverse=False):
    core_dir = os.path.dirname(core_path(project))
    plan = []
    for patch in info["patches"]:
        target = os.path.join(core_dir, patch["file"])
        if not os.path.exists(target):
            raise ManagerError(f"{target} was not found")
        text = read_text(target)
        find, replace = (patch["replace"], patch["find"]) if reverse else (patch["find"], patch["replace"])
        if find in text:
            if text.count(find) != 1:
                raise ManagerError(f"The fix does not fit {patch['file']}: the place is not unique")
            plan.append((target, text.replace(find, replace)))
        elif replace not in text:
            raise ManagerError(f"The fix does not fit {patch['file']}: the file was changed by hand")
    for target, new_text in plan:
        backup(target, info["id"])
        write_text(target, new_text)
    cfg = read_config(project)
    fixes = cfg.setdefault("hotfixes", [])
    if reverse and info["id"] in fixes:
        fixes.remove(info["id"])
    elif not reverse and info["id"] not in fixes:
        fixes.append(info["id"])
    write_config(project, cfg)
    verb = "Reverted" if reverse else "Applied"
    return [f"{verb} fix '{info['id']}' ({len(plan)} change(s) in {core_dir})"]


def import_plugin(json_path):
    json_path = os.path.abspath(json_path)
    plugin_id = os.path.splitext(os.path.basename(json_path))[0]
    if not plugin_id.isidentifier():
        raise ManagerError("The plugin id (the file name) must be letters, digits and underscores")
    try:
        info = json.loads(read_text(json_path))
    except (OSError, json.JSONDecodeError) as error:
        raise ManagerError(f"Cannot read {json_path}: {error}")
    if info.get("patches"):
        raise ManagerError("Imported user plugins cannot contain patches. Hotfixes ship with Worse Code")
    code_name = info.get("file", plugin_id + ".py")
    code_source = os.path.join(os.path.dirname(json_path), code_name)
    if not os.path.exists(code_source):
        raise ManagerError(f"{code_name} must lie next to {os.path.basename(json_path)}")
    os.makedirs(CATALOG_DIR, exist_ok=True)
    for source, name in ((json_path, plugin_id + ".json"), (code_source, code_name)):
        target = os.path.join(CATALOG_DIR, name)
        if not same_path(source, target):
            shutil.copy2(source, target)
    data = read_list()
    if not any(plugin_id in ids for ids in data.values()):
        data["user"].append(plugin_id)
        write_list(data)
    return [f"Imported '{plugin_id}' into the User category"]


def status_of(project, info):
    if not project or not os.path.isdir(project) or info.get("broken"):
        return ""
    if info["category"] == "hotfix":
        return "applied" if hotfix_applied(project, info) else ""
    return "installed" if info["id"] in read_config(project).get("plugins", []) else ""


def describe(info):
    lines = [f"{info['name']}  (v{info['version']}, {TITLES.get(info['category'], info['category'])})"]
    if info.get("author"):
        lines.append(f"by {info['author']}")
    lines += ["", info["description"] or "No description."]
    if info["commands"]:
        lines += ["", "Commands: " + ", ".join(f"{key} (default word: {word})" for key, word in info["commands"].items())]
    if info["functions"]:
        lines.append("Functions: " + ", ".join(info["functions"]))
    if info["depends"]:
        lines.append("Needs: " + ", ".join(info["depends"]))
    if info["example"]:
        lines += ["", "Example:", "  " + info["example"]]
    if info["category"] == "hotfix":
        lines += ["", "Changes: " + ", ".join(sorted({p["file"] for p in info.get("patches", [])}))]
    return "\n".join(lines)


def run_gui(initial):
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk

    root = tk.Tk()
    root.title("WC Plugin Manager")
    root.geometry("920x580")
    project = tk.StringVar(value=initial or "")
    state = tk.StringVar()
    infos = {}

    top = ttk.Frame(root)
    top.pack(fill="x", padx=10, pady=8)
    ttk.Label(top, text="Project folder:").pack(side="left")
    ttk.Entry(top, textvariable=project).pack(side="left", fill="x", expand=True, padx=6)
    ttk.Label(root, textvariable=state, foreground="gray").pack(fill="x", padx=10)

    middle = ttk.Frame(root)
    middle.pack(fill="both", expand=True, padx=10, pady=8)
    tree = ttk.Treeview(middle, columns=("version", "status"), height=18)
    tree.heading("#0", text="Plugin")
    tree.heading("version", text="Version")
    tree.heading("status", text="Status")
    tree.column("#0", width=280)
    tree.column("version", width=70, anchor="center")
    tree.column("status", width=90, anchor="center")
    tree.pack(side="left", fill="y")
    details = tk.Text(middle, wrap="word", state="disabled", width=60)
    details.pack(side="left", fill="both", expand=True, padx=(10, 0))

    def current_project():
        return project.get().strip().strip('"')

    def selected():
        picked = tree.selection()
        return picked[0] if picked and picked[0] in infos else None

    def show_details(event=None):
        plugin_id = selected()
        details.configure(state="normal")
        details.delete("1.0", "end")
        if plugin_id:
            details.insert("1.0", describe(infos[plugin_id]))
        details.configure(state="disabled")

    def refresh():
        folder = current_project()
        tree.delete(*tree.get_children())
        infos.clear()
        items = catalog()
        for category in CATEGORIES:
            tree.insert("", "end", iid="category:" + category, text=TITLES[category], open=True)
        for info in items:
            infos[info["id"]] = info
            try:
                status = status_of(folder, info)
            except ManagerError:
                status = "?"
            tree.insert("category:" + info["category"], "end", iid=info["id"], text=info["name"],
                        values=(info["version"], status))
        if folder and os.path.isdir(folder):
            try:
                path, ready = support_state(folder)
                state.set(f"Core: {path}   Plugin support: {'on' if ready else 'off (installing a plugin turns it on)'}")
            except OSError as error:
                state.set(str(error))
        else:
            state.set("Choose a project folder to install plugins into.")
        show_details()

    def browse():
        folder = filedialog.askdirectory(title="Choose the project folder")
        if folder:
            project.set(folder)
            refresh()

    def attempt(action):
        try:
            return action()
        except CoreError as error:
            if messagebox.askyesno("wc.py was customized", f"{error}.\n\nReplace it with the latest wc.py? A backup is saved next to it."):
                try:
                    enable_support(current_project(), replace=True)
                    return attempt(action)
                except ManagerError as second:
                    messagebox.showerror("Plugin Manager", str(second))
        except ManagerError as error:
            messagebox.showerror("Plugin Manager", str(error))
        return None

    def do_install():
        plugin_id = selected()
        if not plugin_id:
            return
        renames = {}

        def action():
            while True:
                try:
                    return install(current_project(), plugin_id, renames)
                except ConflictError as error:
                    for key, word, owner in error.conflicts:
                        new = simpledialog.askstring("Keyword conflict", f"The word '{word}' ({key}) is already used by {owner}.\nChoose another word:", parent=root)
                        if not new:
                            raise ManagerError("Installation cancelled")
                        renames[key] = new.strip()

        notes = attempt(action)
        if notes:
            messagebox.showinfo("Plugin Manager", "\n".join(notes))
        refresh()

    def do_remove():
        plugin_id = selected()
        if not plugin_id:
            return
        notes = attempt(lambda: remove(current_project(), plugin_id))
        if notes:
            messagebox.showinfo("Plugin Manager", "\n".join(notes))
        refresh()

    def do_enable():
        notes = attempt(lambda: enable_support(current_project()))
        messagebox.showinfo("Plugin Manager", "\n".join(notes) if notes else "Plugin support is already on.")
        refresh()

    def do_import():
        path = filedialog.askopenfilename(title="Choose the plugin .json file", filetypes=[("Plugin description", "*.json")])
        if not path:
            return
        try:
            messagebox.showinfo("Plugin Manager", "\n".join(import_plugin(path)))
        except ManagerError as error:
            messagebox.showerror("Plugin Manager", str(error))
        refresh()

    buttons = ttk.Frame(root)
    buttons.pack(fill="x", padx=10, pady=(0, 10))
    for text, command in (("Browse...", browse), ("Install / Apply fix", do_install), ("Remove / Revert fix", do_remove),
                          ("Enable plugin support", do_enable), ("Import user plugin...", do_import), ("Refresh", refresh)):
        ttk.Button(buttons, text=text, command=command).pack(side="left", padx=4)

    tree.bind("<<TreeviewSelect>>", show_details)
    refresh()
    root.mainloop()


def print_list(project):
    for category in CATEGORIES:
        items = [info for info in catalog() if info["category"] == category]
        print(TITLES[category])
        for info in items:
            status = status_of(project, info)
            print(f"  {info['id']:<18} v{info['version']:<6} {('[' + status + ']') if status else '':<12} {info['description'][:70]}")
        if not items:
            print("  (none)")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wc_plugin_manager", description="Install Worse Code plugins into a project folder.")
    parser.add_argument("project", nargs="?", help="the project folder")
    parser.add_argument("--list", action="store_true", help="show all plugins")
    parser.add_argument("--install", metavar="ID", action="append", help="install a plugin or apply a hotfix")
    parser.add_argument("--remove", metavar="ID", action="append", help="remove a plugin or revert a hotfix")
    parser.add_argument("--rename", metavar="KEY=WORD", action="append", default=[], help="use another keyword for a plugin command")
    parser.add_argument("--enable-support", action="store_true", help="add plugin hooks to wc.py")
    parser.add_argument("--replace-core", action="store_true", help="with --enable-support: replace wc.py with the latest one")
    parser.add_argument("--import", dest="import_path", metavar="PLUGIN.json", help="add a user plugin to the catalog")
    args = parser.parse_args(argv)

    if not (args.list or args.install or args.remove or args.enable_support or args.import_path):
        return run_gui(args.project)
    try:
        if args.import_path:
            print("\n".join(import_plugin(args.import_path)))
        if args.list:
            print_list(args.project)
        if args.enable_support:
            check_project(args.project)
            print("\n".join(enable_support(args.project, args.replace_core) or ["Plugin support is already on."]))
        renames = dict(item.split("=", 1) for item in args.rename if "=" in item)
        for plugin_id in args.install or []:
            print("\n".join(install(args.project, plugin_id, renames)))
        for plugin_id in args.remove or []:
            print("\n".join(remove(args.project, plugin_id)))
    except ManagerError as error:
        print(f"Error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
