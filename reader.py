#!/usr/bin/env python3
"""Speed reader: shows text one word at a time in the same spot, so your eyes don't move.

Paste text or open a .txt / .md file, pick a speed, press Space.
Keys: Space start/pause, Left back one sentence, Right forward one sentence, Up/Down speed, Esc back to text.

Good for light reading and for getting through easy material. For hard material read normally:
comprehension drops when you can't glance back (Rayner et al. 2016). Left is there so you can.
"""
import re
import sys
import tkinter as tk
from tkinter import filedialog

from common import BG, BLUE, DIM, FG, FONT, HOT, PANEL, button

SENTENCE_END = re.compile(r'[.!?]["\')\]]*$')


def words(text):
    """Split into words, dropping markdown symbols that don't read well one at a time."""
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.M)          # headings
    text = re.sub(r"[*_`]{1,3}", "", text)                       # emphasis and code marks
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)          # [link](url) -> link
    return text.split()


def focus_index(word):
    """The letter the eye should land on: a bit left of center, the way readers fixate words."""
    n = len(word.strip(".,;:!?\"'()[]"))
    return 0 if n <= 1 else 1 if n <= 5 else 2 if n <= 9 else 3 if n <= 13 else 4


def delay_ms(word, wpm):
    """Time to show a word. Longer words and the ends of clauses and sentences get extra time."""
    base = 60000 / wpm
    if SENTENCE_END.search(word):
        base *= 2.2
    elif word[-1:] in ",;:":
        base *= 1.5
    if len(word) > 8:
        base *= 1.3
    return int(base)


def sentence_starts(ws):
    starts = [0]
    for i, w in enumerate(ws[:-1]):
        if SENTENCE_END.search(w):
            starts.append(i + 1)
    return starts


class Reader(tk.Tk):
    def __init__(self, path=None):
        super().__init__()
        self.title("Speed Reader")
        self.geometry("900x560")
        self.configure(bg=BG)
        self.ws, self.i, self.job = [], 0, None
        self.wpm = tk.IntVar(value=300)
        self.build_text_screen()
        if path:
            self.load(path)

    # ---- screen 1: the text
    def build_text_screen(self):
        self.text_frame = f = tk.Frame(self, bg=BG)
        f.pack(fill="both", expand=True, padx=24, pady=16)
        tk.Label(f, text="Paste text below or open a file, then press Start.", bg=BG, fg=DIM,
                 font=(FONT, 11)).pack(anchor="w")
        self.box = tk.Text(f, bg=PANEL, fg=FG, insertbackground=FG, font=(FONT, 12), wrap="word",
                           relief="flat", padx=12, pady=10)
        self.box.pack(fill="both", expand=True, pady=8)
        row = tk.Frame(f, bg=BG)
        row.pack(fill="x")
        button(row, "Open file", self.pick_file, color=PANEL).pack(side="left")
        tk.Label(row, text="  Words a minute", bg=BG, fg=FG, font=(FONT, 11)).pack(side="left")
        tk.Scale(row, from_=100, to=900, resolution=25, orient="horizontal", variable=self.wpm, length=260,
                 bg=BG, fg=FG, highlightthickness=0, troughcolor=PANEL).pack(side="left", padx=8)
        button(row, "Start (Space)", self.start).pack(side="right")
        self.bind("<space>", lambda e: self.start() if self.focus_get() is not self.box else None)

    def pick_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt *.md"), ("All files", "*")])
        if path:
            self.load(path)

    def load(self, path):
        with open(path, encoding="utf-8", errors="replace") as f:
            self.box.delete("1.0", "end")
            self.box.insert("1.0", f.read())

    # ---- screen 2: one word at a time
    def start(self):
        self.ws = words(self.box.get("1.0", "end"))
        if not self.ws:
            return
        self.starts = sentence_starts(self.ws)
        self.text_frame.pack_forget()
        self.unbind("<space>")
        self.view = v = tk.Frame(self, bg=BG)
        v.pack(fill="both", expand=True)
        self.status = tk.Label(v, bg=BG, fg=DIM, font=(FONT, 11))
        self.status.pack(pady=(18, 0))
        self.canvas = tk.Canvas(v, bg=BG, highlightthickness=0, height=200)
        self.canvas.pack(fill="x", expand=True)
        tk.Label(v, text="Space pause   Left/Right sentence   Up/Down speed   Esc back to the text",
                 bg=BG, fg=DIM, font=(FONT, 10)).pack(pady=12)
        for key, fn in (("<space>", self.toggle), ("<Left>", lambda e: self.jump(-1)),
                        ("<Right>", lambda e: self.jump(1)), ("<Up>", lambda e: self.speed(25)),
                        ("<Down>", lambda e: self.speed(-25)), ("<Escape>", self.back)):
            self.bind(key, fn)
        self.i, self.paused = 0, False
        self.after(400, self.tick)

    def draw(self):
        c = self.canvas
        c.delete("all")
        w = self.ws[self.i]
        k = focus_index(w)
        cx, cy = self.winfo_width() // 2, 100
        font = (FONT, 40)
        left = c.create_text(0, cy, text=w[:k], font=font, anchor="e")
        mid = c.create_text(0, cy, text=w[k:k + 1], font=font, anchor="w", fill=HOT)
        right = c.create_text(0, cy, text=w[k + 1:], font=font, anchor="w")
        mw = c.bbox(mid)[2] - c.bbox(mid)[0] if w[k:k + 1] else 0
        c.coords(left, cx - mw / 2, cy)
        c.coords(mid, cx - mw / 2, cy)
        c.coords(right, cx + mw / 2, cy)
        c.itemconfig(left, fill=FG)
        c.itemconfig(right, fill=FG)
        c.create_line(cx, cy - 46, cx, cy - 34, fill=DIM, width=2)
        c.create_line(cx, cy + 34, cx, cy + 46, fill=DIM, width=2)
        left_min = (len(self.ws) - self.i) / self.wpm.get()
        self.status.config(text=f"{self.wpm.get()} wpm   word {self.i + 1} of {len(self.ws)}   "
                                f"about {left_min:.0f} min left" + ("   PAUSED" if self.paused else ""))

    def tick(self):
        self.job = None
        if self.paused:
            return
        self.draw()
        delay = delay_ms(self.ws[self.i], self.wpm.get())
        if self.i + 1 < len(self.ws):
            self.i += 1
            self.job = self.after(delay, self.tick)
        else:
            self.paused = True
            self.status.config(text="Done. Esc to go back, Left to go over the last sentence.")

    def toggle(self, _=None):
        self.paused = not self.paused
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        if self.paused:
            self.i = max(0, self.i - 1)
            self.draw()
        else:
            self.tick()

    def jump(self, step):
        cur = max(s for s in self.starts if s <= max(0, self.i - 1))
        n = self.starts.index(cur) + step
        self.i = self.starts[min(max(n, 0), len(self.starts) - 1)]
        if self.paused:
            self.draw()

    def speed(self, d):
        self.wpm.set(min(900, max(100, self.wpm.get() + d)))
        if self.paused:
            self.draw()

    def back(self, _=None):
        if self.job:
            self.after_cancel(self.job)
        for key in ("<space>", "<Left>", "<Right>", "<Up>", "<Down>", "<Escape>"):
            self.unbind(key)
        self.view.destroy()
        self.text_frame.pack(fill="both", expand=True, padx=24, pady=16)
        self.bind("<space>", lambda e: self.start() if self.focus_get() is not self.box else None)


if __name__ == "__main__":
    Reader(sys.argv[1] if len(sys.argv) > 1 else None).mainloop()
