#!/usr/bin/env python3
"""Colemak typing trainer. Type on your normal QWERTY keyboard; each key is read as its Colemak letter,
so you can learn the layout without changing any system settings.

Five lessons add letters a few at a time, starting from the home row. Keys 1-5 switch lessons.
"""
import random, time
import tkinter as tk

QW = "qwertyuiopasdfghjkl;zxcvbnm"
CM = "qwfpgjluy;arstdhneiozxcvbkm"
TO_CM = dict(zip(QW, CM))
ROWS = ["qwertyuiop", "asdfghjkl;", "zxcvbnm"]

LESSONS = [("Home row", "arstneio"), ("+ d h", "arstneiodh"), ("+ f p l u", "arstneiodhfplu"),
           ("+ g j y w q", "arstneiodhfplugjywq"), ("All letters", "arstneiodhfplugjywqcvbkmxz")]
WORDS = """the and for are but not you all any can had her was one our out day get has him his how man new
now old see two way who boy did its let put say she too use that with have this will your from they know
want been good much some time very when come here just like long make many more only over such take than
them well were rest tree near tone seat rain star note stone train tire site iron onion toast straw rose
nose arts eats oats sister senior retain orient snore tennis inert noise into sea ten tea set sit eat ate
air art rat ran nor son sort store stair trait rent tent toe tie those then three heat hand dish shed third
drain other their these there said told need road hint hid hide dirt dear head horse north shoe share dose
idea fold full play plus fluid apple until pure plan pill lift loud soup flour help half path pupil quiet
joy gift yellow world quick jump young why whip query gray weight glow judge fox lazy brown back move voice
cake zone box black mix work vex kick make big cozy maze""".split()

BG, FG, KEY, DIM, GREEN, RED, BLUE = "#1e1e24", "#eeeeee", "#33333a", "#77777f", "#66cc66", "#aa3333", "#5588cc"
S = dict(lesson=0, text="", pos=0, bad=False, start=0, chars=0, total=0, errors=0)

root = tk.Tk()
root.title("Colemak Trainer")
root.configure(bg=BG, padx=24, pady=16)

bar = tk.Frame(root, bg=BG)
bar.pack()
buttons = [tk.Button(bar, text=f"{i + 1}. {n}", command=lambda i=i: pick(i), fg=FG, bd=0, padx=10, pady=4,
                     activebackground=BLUE, activeforeground=FG, takefocus=0)
           for i, (n, _) in enumerate(LESSONS)]
for b in buttons:
    b.pack(side="left", padx=3)
stats = tk.Label(root, bg=BG, fg=FG, font=("Sans", 12))
stats.pack(pady=(12, 0))
txt = tk.Text(root, width=44, height=2, wrap="word", bg=BG, fg=FG, bd=0, highlightthickness=0,
              font=("Monospace", 26), cursor="arrow")
txt.tag_config("done", foreground=GREEN)
txt.tag_config("cur", background=BLUE)
txt.tag_config("bad", background=RED)
txt.pack(pady=16)
kb = tk.Canvas(root, width=690, height=200, bg=BG, highlightthickness=0)
kb.pack()
tk.Label(root, bg=BG, fg=DIM, font=("Sans", 10),
         text="Big letter = Colemak, small = the key printed on your laptop. Underlined = index fingers rest here. "
              "Keys 1-5 change lesson.").pack(pady=(8, 0))


def new_line():
    pool = [w for w in WORDS if set(w) <= set(LESSONS[S["lesson"]][1])]
    S.update(text=" ".join(random.choice(pool) for _ in range(8)), pos=0, bad=False)


def pick(i):
    S.update(lesson=i, start=0, chars=0, total=0, errors=0)
    new_line()
    render()


def render():
    letters, text, pos = LESSONS[S["lesson"]][1], S["text"], S["pos"]
    for i, b in enumerate(buttons):
        b.config(bg=BLUE if i == S["lesson"] else KEY)
    mins = (time.time() - S["start"]) / 60 if S["start"] else 0
    wpm = round(S["chars"] / 5 / mins) if mins else 0
    acc = round(100 * (S["total"] - S["errors"]) / S["total"]) if S["total"] else 100
    stats.config(text=f"WPM {wpm}    Accuracy {acc}%")
    txt.config(state="normal")
    txt.delete("1.0", "end")
    txt.insert("1.0", text[:pos], "done", text[pos], "bad" if S["bad"] else "cur", text[pos + 1:])
    txt.config(state="disabled")
    kb.delete("all")
    for r, row in enumerate(ROWS):
        for j, q in enumerate(row):
            c, x, y = TO_CM[q], 10 + r * 25 + j * 64, 5 + r * 64
            kb.create_rectangle(x, y, x + 58, y + 58, fill=BLUE if c == text[pos] else KEY, outline="")
            kb.create_text(x + 29, y + 24, text=c, fill=FG if c in letters else DIM, font=("Sans", 20))
            kb.create_text(x + 29, y + 47, text=q.upper(), fill=DIM, font=("Sans", 9))
            if c in "tn":
                kb.create_line(x + 20, y + 55, x + 38, y + 55, fill=FG, width=2)


def on_key(e):
    k = e.char.lower()
    if k in ("1", "2", "3", "4", "5"):
        return pick(int(k) - 1)
    ch = " " if k == " " else TO_CM.get(k)
    if not ch:
        return
    S["start"] = S["start"] or time.time()
    S["total"] += 1
    if ch == S["text"][S["pos"]]:
        S.update(pos=S["pos"] + 1, chars=S["chars"] + 1, bad=False)
        if S["pos"] == len(S["text"]):
            new_line()
    else:
        S.update(errors=S["errors"] + 1, bad=True)
    render()


root.bind("<Key>", on_key)
pick(0)

if __name__ == "__main__":
    root.mainloop()
