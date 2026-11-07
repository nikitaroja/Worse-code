import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from wc import DEFAULTS, CONFIG_PATH, BASE, load_config
from wcsg import PRESETS, POSITIONS

# (ключ в конфиге, описание, пример для справки)
COMMANDS = [
    ("say", "Вывод на экран", '{kw} "Привет, мир"'),
    ("set", "Создать переменную", "{kw} x = 5"),
    ("ask", "Спросить число или текст", "{kw} x"),
    ("if", "Если условие верно, выполнить блок", "{kw} x > 3"),
    ("else", "Иначе (необязательно)", "{kw}"),
    ("end", "Конец блока if", "{kw}"),
    ("load", "Подключить модуль", "{kw} standrt_gui"),
    ("gui_start", "Начало зоны WCSG (окна)", "{kw}"),
    ("gui_stop", "Конец зоны WCSG", "{kw}"),
    ("while", "Повторять, пока условие верно", "{kw} alive"),
    ("for", "Пройти по списку (x in список)", "{kw} seg in body"),
    ("break", "Выйти из цикла", "{kw}"),
    ("do", "Выполнить действие (например со списком)", "{kw} body.append([1, 2])"),
    ("canvas", "Открыть холст (ширина, высота, фон)", "{kw} 600, 600, \"black\""),
    ("text", "Надпись на холсте", "{kw} 10, 10, \"Score\", \"white\", 18"),
    ("force_noecho", "Навсегда скрыть консоль (всё через окна)", "{kw}"),
    ("comment", "Комментарий (строка игнорируется)", "{kw} это заметка"),
    ("prompt", "Символ приглашения при вводе", None),
]

# Эти команды должны быть одним словом и не повторяться
WORD_KEYS = ["say", "set", "ask", "if", "else", "end", "load", "gui_start", "gui_stop", "force_noecho",
             "while", "for", "break", "do", "canvas", "text"]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WC Service Modifier")
        self.geometry("720x860")
        self.cfg = load_config()

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)
        self.tab_cmd = ttk.Frame(tabs)
        self.tab_help = ttk.Frame(tabs)
        self.tab_run = ttk.Frame(tabs)
        tabs.add(self.tab_cmd, text="Команды")
        tabs.add(self.tab_help, text="Справка")
        tabs.add(self.tab_run, text="Запуск")

        self.build_commands()
        self.build_help()
        self.build_run()
        self.refresh_help()

    # ---------- Вкладка «Команды» ----------
    def build_commands(self):
        f = self.tab_cmd
        self.entries = {}
        ttk.Label(
            f, text="Впиши свои слова для команд WC:",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10)

        for i, (key, desc, _) in enumerate(COMMANDS, start=1):
            ttk.Label(f, text=desc).grid(row=i, column=0, sticky="w", padx=10, pady=4)
            ttk.Label(f, text=f"(по умолчанию: {DEFAULTS[key]!r})", foreground="gray") \
                .grid(row=i, column=1, padx=6)
            entry = ttk.Entry(f, width=16)
            entry.insert(0, self.cfg[key])
            entry.grid(row=i, column=2, padx=10)
            self.entries[key] = entry

        buttons = ttk.Frame(f)
        buttons.grid(row=len(COMMANDS) + 1, column=0, columnspan=3, pady=14)
        ttk.Button(buttons, text="Сохранить", command=self.save).pack(side="left", padx=6)
        ttk.Button(buttons, text="Вернуть по умолчанию", command=self.reset).pack(side="left", padx=6)

        ttk.Label(
            f, foreground="gray", wraplength=660, justify="left",
            text="Команды (кроме комментария и приглашения) должны быть одним словом, "
                 "без пробелов и не повторяться. "
                 "Изменения сохраняются в wc_config.json рядом с wc.py.",
        ).grid(row=len(COMMANDS) + 2, column=0, columnspan=3, padx=10, sticky="w")

    def save(self):
        new = {}
        for key, entry in self.entries.items():
            new[key] = entry.get() if key == "prompt" else entry.get().strip()

        words = [new[k] for k in WORD_KEYS]
        if any((not w) or (" " in w) for w in words):
            messagebox.showerror("Ошибка", "Команды не могут быть пустыми или содержать пробелы.")
            return
        if len(set(words)) < len(words):
            messagebox.showerror("Ошибка", "Все команды должны быть разными.")
            return
        if not new["comment"]:
            messagebox.showerror("Ошибка", "Символ комментария не может быть пустым.")
            return
        if any(w.startswith(new["comment"]) for w in words):
            messagebox.showerror("Ошибка", "Команда не может начинаться с символа комментария.")
            return

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(new, f, ensure_ascii=False, indent=2)
        self.cfg = new
        self.refresh_help()
        messagebox.showinfo("Готово", "Настройки сохранены!")

    def reset(self):
        for key, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, DEFAULTS[key])

    # ---------- Вкладка «Справка» ----------
    def build_help(self):
        frame = self.tab_help
        self.help_text = tk.Text(frame, wrap="word", font=("Consolas", 10), state="disabled")
        scroll = ttk.Scrollbar(frame, command=self.help_text.yview)
        self.help_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.help_text.pack(fill="both", expand=True)

    def refresh_help(self):
        c = self.cfg
        lines = [
            "WC (Worse Code) — справка",
            "",
            "КАК ЗАПУСТИТЬ",
            "  python wc.py программа.wc",
            "",
            "КОМАНДЫ (с твоими текущими словами)",
        ]
        for key, desc, example in COMMANDS:
            if example:
                lines.append(f"  {c[key]}   — {desc}")
                lines.append("      пример: " + example.format(kw=c[key]))
        lines += [
            "",
            "УСЛОВИЯ",
            "  Сравнения: ==  !=  <  >  <=  >=   Связки: and, or, not",
            "  Сколько if, столько и end. Блоки можно вкладывать друг в друга.",
            "  Комментарий можно писать и в конце строки.",
            "",
            "ПРИМЕР: КАЛЬКУЛЯТОР (+ и -)",
            f'  {c["say"]} "Первое число:"',
            f'  {c["ask"]} a',
            f'  {c["say"]} "Операция (+ или -):"',
            f'  {c["ask"]} op',
            f'  {c["say"]} "Второе число:"',
            f'  {c["ask"]} b',
            f'  {c["if"]} op == "+"',
            f'      {c["say"]} a + b',
            f'  {c["else"]}',
            f'      {c["say"]} a - b',
            f'  {c["end"]}',
            "",
            "МОДУЛЬ WCSG (WC Standart GUI): окна",
            f'  {c["load"]} standrt_gui   подключить модуль (один раз в начале)',
            f'  {c["gui_start"]} ... {c["gui_stop"]}   между ними пишутся окна',
            "  Формат строки:  Окно ] параметр значение ] параметр значение",
            "  Параметры:",
            "    where       место на экране: " + ", ".join(POSITIONS),
            "    speak       текст окна (можно выражение: speak (\"Привет, \" + name))",
            "    title       заголовок окна",
            "    fontspeak   шрифт, например \"Arial Black\"",
            "    fontsize    размер шрифта",
            "    windowicon  картинка возле текста (png/gif, jpg нужен Pillow)",
            "                путь считается от папки с .wc файлом",
            "    bg / fg     цвет фона / текста, например \"#ffeeee\" или \"red\"",
            "    save        сохранить ответ окна в переменную",
            "    size        размер окна: size \"400x200\"",
            "    alpha       прозрачность 0.1-1, например alpha 0.9",
            "    resizable   можно растягивать окно (yes/no)",
            "    draggable   тянуть окно за любое место (yes/no)",
            "    noborder    убрать рамку и заголовок окна",
            "    topmost     поверх всех окон (yes/no, по умолчанию yes)",
            "    stndrt_icon_destroy  убрать иконку-перо из заголовка окна",
            "    button      кнопка, можно несколько: button \"Play\" ] button \"Quit\"",
            "                нажатие любой закрывает окно, текст кнопки идёт в save",
            "    anykey      любая клавиша закрывает окно (имя клавиши идёт в save)",
            "  Окна-пресеты:",
        ]
        for name, preset in PRESETS.items():
            lines.append(f"    {name.capitalize():<16} {preset['about']}")
        lines += [
            "",
            "  Пример:",
            f'    {c["load"]} standrt_gui',
            f'    {c["gui_start"]}',
            '    Error_window ] where center ] speak ("тест") ] fontspeak "Arial Black" ] windowicon "/error.jpg"',
            '    Question_window ] speak ("Выйти?") ] save ans',
            f'    {c["gui_stop"]}',
            f'    {c["if"]} ans == "yes"',
            f'        {c["say"]} "Пока!"',
            f'    {c["end"]}',
            "",
            "ЦИКЛЫ, СПИСКИ, СЛУЧАЙНОСТЬ",
            f'  {c["while"]} условие ... {c["end"]}   повторять, пока условие верно',
            f'  {c["for"]} x in список ... {c["end"]}   пройти по каждому элементу, например range(10)',
            f'  {c["break"]}   выйти из цикла досрочно',
            f'  {c["do"]} выражение   выполнить действие без вывода: {c["do"]} body.append([1, 2])',
            "  random(a, b)   случайное целое от a до b (в выражениях)",
            f'  {c["set"]} a, b = 1, 2   или   {c["set"]} body[0] = 5   присваивание частей',
            "",
            "ХОЛСТ MINIPAINT (внутри зоны WCSG)",
            f'  {c["canvas"]} 600, 600, \"black\"   холст: ширина, высота, фон',
            "  clear   стереть холст",
            "  rect x, y, w, h, \"green\"   прямоугольник",
            "  circle x, y, r, \"red\"   круг (центр и радиус)",
            f'  {c["text"]} x, y, \"Score\", \"white\", 16   надпись (размер необязателен)',
            "  waitkey(150)   подождать 150 мс, вернуть последнюю клавишу (\"Up\", \"Left\") или \"\"",
            "",
            "КОНСОЛЬ WCSG",
            "  Между wcsgstart и wcsgstophere обычная консоль скрыта:",
            "    say пишет в чёрное окно, ask открывает поле ввода (Enter или Done).",
            "  В конце зоны окно закрывается по любой клавише или клику.",
            f'  {c["force_noecho"]}   навсегда скрыть консоль (всё идёт через окна)',
            "",
            "ЧТО МЫ УЖЕ ПРОШЛИ",
            "  1. Интерпретатор: wc.py читает файл .wc строка за строкой.",
            "  2. Переменные, вывод и ввод (число или текст).",
            "  3. Выражения считает Python: + - * / и скобки.",
            "  4. Текст в кавычках, число в текст превращается через str(...).",
            "  5. Комментарии, в том числе в конце строки.",
            "  6. Настройки команд лежат в wc_config.json, их меняет этот Modifier.",
            "  7. При ошибке WC пишет номер строки, где она случилась.",
            "  8. Условия: if / else / end, сравнения, and / or / not.",
            "  9. Модули: load и зона WCSG с окнами-пресетами.",
            "  10. Циклы, списки, random и холст MiniPaint: можно писать игры.",
            "",
            "ДАЛЬШЕ В ПЛАНАХ",
            "  функции, мышь на холсте, звуки.",
            "  Цель на год: калькулятор и змейка на WC.",
        ]
        self.help_text.configure(state="normal")
        self.help_text.delete("1.0", "end")
        self.help_text.insert("1.0", "\n".join(lines))
        self.help_text.configure(state="disabled")

    # ---------- Вкладка «Запуск» ----------
    def build_run(self):
        f = self.tab_run
        ttk.Label(
            f, text="Выбери файл .wc, и он запустится в новом окне консоли.",
            wraplength=600,
        ).pack(padx=10, pady=(20, 10), anchor="w")
        ttk.Button(f, text="Выбрать и запустить .wc", command=self.run_file).pack(padx=10, anchor="w")

    def run_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("WC программы", "*.wc"), ("Все файлы", "*.*")]
        )
        if not path:
            return
        wc = os.path.join(BASE, "wc.py")
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen([sys.executable, wc, path, "--pause"], creationflags=flags)


if __name__ == "__main__":
    App().mainloop()
