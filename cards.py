#!/usr/bin/env python3
"""Flashcards with spaced review. Cards you know come back less and less often; cards you miss come back tomorrow.

  python3 cards.py                 pick a card file from the cards/ folder
  python3 cards.py cards/my.txt    review that file

A card file is plain text, one card per line:   question :: answer
Lines starting with # are comments. Edit the file any time; progress is kept by question text.

Keys: Space show the answer, 1 missed it, 2 got it.
Boxes: a card moves up a box each time you get it (1, 2, 4, 8, 16, 32 days), and back to box 1 when you miss it.
"""
import datetime as dt
import hashlib
import random
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from common import BG, DATA, DIM, FG, FONT, GOOD, HERE, BAD, button, load_json, save_json

INTERVALS = [1, 2, 4, 8, 16, 32]


def parse(text):
    cards = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "::" not in line:
            continue
        q, a = (s.strip() for s in line.split("::", 1))
        if q and a:
            cards.append((q, a))
    return cards


def key(q):
    return hashlib.sha1(q.encode("utf-8")).hexdigest()[:16]


def due(cards, progress, on):
    on = on.isoformat()
    return [c for c in cards if progress.get(key(c[0]), {}).get("due", "") <= on]


def grade(progress, q, got_it, on):
    p = progress.setdefault(key(q), {"box": 0})
    p["box"] = min(p["box"] + 1, len(INTERVALS) - 1) if got_it else 0
    p["due"] = (on + dt.timedelta(days=INTERVALS[p["box"]] if got_it else 1)).isoformat()
    return p


class Cards(tk.Tk):
    def __init__(self, path):
        super().__init__()
        self.path = Path(path)
        self.state_file = DATA / "cards" / f"{self.path.stem}-{key(str(self.path.resolve()))}.json"
        self.progress = load_json(self.state_file, {})
        self.cards = parse(self.path.read_text(encoding="utf-8"))
        self.queue = due(self.cards, self.progress, dt.date.today())
        random.shuffle(self.queue)
        self.retry = set()   # missed today: shown again, but the schedule already says tomorrow
        self.done_count = self.missed = 0
        self.title(f"Cards: {self.path.stem}")
        self.geometry("760x480")
        self.configure(bg=BG)
        self.bind("<space>", lambda e: self.reveal())
        self.bind("1", lambda e: self.answer(False))
        self.bind("2", lambda e: self.answer(True))
        self.show()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def label(self, text, size, color=FG, bold=False):
        l = tk.Label(self, text=text, bg=BG, fg=color, font=(FONT, size, "bold" if bold else "normal"),
                     wraplength=680, justify="center")
        l.pack(pady=8)
        return l

    def show(self):
        self.clear()
        self.revealed = False
        tk.Frame(self, bg=BG, height=24).pack()
        if not self.queue:
            nxt = min((p["due"] for p in self.progress.values() if "due" in p), default=None)
            self.label("All caught up.", 22, GOOD, True)
            self.label(f"Reviewed {self.done_count}, missed {self.missed}. "
                       + (f"Next cards are due {nxt}." if nxt else ""), 12, DIM)
            return
        self.label(f"{len(self.queue)} left today   ·   {len(self.cards)} cards in this file", 10, DIM)
        self.label(self.queue[0][0], 20, bold=True)
        self.answer_label = self.label("", 16, "#cfe3ff")
        self.hint = self.label("Say the answer to yourself, then press Space.", 11, DIM)
        self.row = tk.Frame(self, bg=BG)
        self.row.pack(side="bottom", pady=24)

    def reveal(self):
        if not self.queue or self.revealed:
            return
        self.revealed = True
        self.answer_label.config(text=self.queue[0][1])
        self.hint.config(text="Did you have it?")
        button(self.row, "1  Missed it", lambda: self.answer(False), color=BAD).pack(side="left", padx=8)
        button(self.row, "2  Got it", lambda: self.answer(True), color=GOOD).pack(side="left", padx=8)

    def answer(self, got_it):
        if not self.revealed:
            return
        q, a = self.queue.pop(0)
        if q not in self.retry:
            grade(self.progress, q, got_it, dt.date.today())
            save_json(self.state_file, self.progress)
            self.done_count += 1
            self.missed += not got_it
        if not got_it:
            self.retry.add(q)
            self.queue.append((q, a))   # once more before you stop today
        self.show()


def main(args):
    path = args[0] if args else None
    if not path:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(initialdir=HERE / "cards", filetypes=[("Cards", "*.txt *.md")])
        root.destroy()
    if path:
        Cards(path).mainloop()


if __name__ == "__main__":
    main(sys.argv[1:])
