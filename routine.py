#!/usr/bin/env python3
"""Book routine: get a non-fiction book into your head in three short sittings and two checks.

Add a book, then each day open this and do what's due. One step on screen at a time, each with its own timer.
What you type goes into a Markdown file per book (in ~/.learning-kit/books/), so your answers stay yours.
When you finish a sitting, the next one is scheduled for you.

Why each step is there is in the README, with the studies behind it.
"""
import datetime as dt
import re
import tkinter as tk
from tkinter import messagebox

from common import BG, BLUE, DATA, DIM, FG, FONT, GOOD, PANEL, button, load_json, save_json

BOOKS = DATA / "books.json"
NOTES = DATA / "books"

# (name, days to wait before this sitting, [(step, minutes, what to do)])
STAGES = [
    ("First look", 0, [
        ("Purpose", 1, "Finish the line: I want ... so that I can ..."),
        ("Preview", 2, "Cover, back cover and contents only. How is the book built? "
                       "Write a one-sentence guess at what it says. Not worth your time? Stop here, that's a win."),
        ("Skim (optional)", 5, "Turn every page. Look only at headings, pictures and anything in bold."),
        ("Trigger words", 8, "Open about every 20 pages and check the index. Write 10 to 25 words that keep coming up."),
        ("Questions", 4, "Turn the words into 3 to 5 questions. Why and how questions work best."),
        ("Stop", 1, "Don't look for answers yet. Decide when and where the next sitting happens. Sleep on it."),
    ]),
    ("Find the answers", 1, [
        ("Read your purpose and questions", 1, "Then take one question at a time."),
        ("Guess", 1, "Say your answer out loud before you look. A wrong guess still helps you learn the right one."),
        ("Find the place", 2, "Contents, or the index entry with the most pages."),
        ("Skim for it", 3, "Eyes down the middle of the page. Nothing jumps out? Read the first sentence of each paragraph."),
        ("Read it properly", 5, "Read the page or two that answers it at your normal pace. Going back over a hard "
                                "sentence is fine."),
        ("Write it from memory", 4, "Close the book. Write the answer in your own words, with the page number and why "
                                    "it matters to you. Open, check, fix. Repeat from Guess for each question."),
    ]),
    ("Say it back", 2, [
        ("Out loud", 2, "Book closed: two minutes on what the book says and what you're taking from it."),
        ("Answer again", 8, "Cover your answers and answer each question again from memory."),
        ("Fix", 5, "Open the book. Fix what you got wrong. Look up anything still not found."),
        ("One action", 3, "Rewrite the one-sentence summary. Write one thing you'll do, with a date."),
    ]),
    ("Check after a week", 5, [
        ("Recall", 5, "Cover your answers. Answer every question from memory. Miss one? Look it up, cover it, "
                      "answer again. Stop when each has come out right once."),
    ]),
    ("Check after a month", 23, [
        ("Recall", 5, "Same as last time. After this the book is done."),
    ]),
]


def slug(title):
    return re.sub(r"[^\w\- ]", "", title).strip().replace(" ", "-")[:80] or "book"


def today():
    return dt.date.today()


def add_book(books, title, on=None):
    on = on or today()
    books[title] = {"stage": 0, "due": on.isoformat(), "added": on.isoformat()}
    return books


def finish_stage(books, title, on=None):
    """Move a book to its next sitting and date it. Returns the next stage name, or None when the book is done."""
    on = on or today()
    b = books[title]
    b["stage"] += 1
    if b["stage"] >= len(STAGES):
        b["done"] = on.isoformat()
        b.pop("due", None)
        return None
    b["due"] = (on + dt.timedelta(days=STAGES[b["stage"]][1])).isoformat()
    return STAGES[b["stage"]][0]


def due_books(books, on=None):
    on = (on or today()).isoformat()
    return sorted((t for t, b in books.items() if "due" in b and b["due"] <= on), key=lambda t: books[t]["due"])


def append_note(title, heading, text):
    NOTES.mkdir(parents=True, exist_ok=True)
    path = NOTES / f"{slug(title)}.md"
    new = not path.exists()
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(f"# {title}\n")
        f.write(f"\n## {heading} ({today().isoformat()})\n\n{text.strip()}\n")
    return path


class Routine(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Book Routine")
        self.geometry("820x600")
        self.configure(bg=BG)
        self.books = load_json(BOOKS, {})
        self.job = None
        self.home()

    def clear(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        for w in self.winfo_children():
            w.destroy()

    def label(self, text, size=12, color=FG, bold=False, parent=None):
        l = tk.Label(parent or self, text=text, bg=BG, fg=color, font=(FONT, size, "bold" if bold else "normal"),
                     wraplength=740, justify="left", anchor="w")
        l.pack(fill="x", padx=30, pady=(0, 8))
        return l

    # ---- home: what's due, add a book
    def home(self):
        self.clear()
        tk.Frame(self, bg=BG, height=16).pack()
        self.label("Due today", 18, bold=True)
        due = due_books(self.books)
        if not due:
            self.label("Nothing due. Add a book below, or come back tomorrow.", 12, DIM)
        for t in due:
            name = STAGES[self.books[t]["stage"]][0]
            button(self, f"{t}  ·  {name}", lambda t=t: self.run(t), anchor="w").pack(fill="x", padx=30, pady=3)
        later = sorted((b["due"], t) for t, b in self.books.items() if "due" in b and t not in due)
        if later:
            self.label("Coming up", 13, DIM).pack_configure(pady=(18, 4))
            for d, t in later[:8]:
                self.label(f"{d}   {t}  ·  {STAGES[self.books[t]['stage']][0]}", 11, DIM)
        done = [t for t, b in self.books.items() if "done" in b]
        if done:
            self.label(f"Finished: {len(done)} book{'s' * (len(done) != 1)}", 11, GOOD).pack_configure(pady=(14, 0))
        row = tk.Frame(self, bg=BG)
        row.pack(side="bottom", fill="x", padx=30, pady=20)
        self.entry = tk.Entry(row, bg=PANEL, fg=FG, insertbackground=FG, font=(FONT, 13), relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=7)
        self.entry.bind("<Return>", lambda e: self.add())
        button(row, "Add book", self.add).pack(side="left", padx=(8, 0))
        self.entry.focus_set()

    def add(self):
        t = self.entry.get().strip()
        if not t:
            return
        if t in self.books:
            messagebox.showinfo("Book Routine", f"'{t}' is already on your list.")
            return
        add_book(self.books, t)
        save_json(BOOKS, self.books)
        self.home()

    # ---- a sitting, one step at a time
    def run(self, title):
        self.title_, self.step = title, 0
        self.stage = STAGES[self.books[title]["stage"]]
        self.notes = []
        self.show_step()

    def show_step(self):
        self.clear()
        name, steps = self.stage[0], self.stage[2]
        step, minutes, what = steps[self.step]
        tk.Frame(self, bg=BG, height=16).pack()
        self.label(f"{self.title_}  ·  {name}  ·  step {self.step + 1} of {len(steps)}", 10, DIM)
        self.label(step, 20, bold=True)
        self.label(what, 13)
        self.left = minutes * 60
        self.clock = tk.Label(self, bg=BG, fg=FG, font=(FONT, 34))
        self.clock.pack(pady=4)
        self.box = tk.Text(self, bg=PANEL, fg=FG, insertbackground=FG, font=(FONT, 12), wrap="word",
                           relief="flat", height=8, padx=10, pady=8)
        self.box.pack(fill="both", expand=True, padx=30, pady=6)
        self.box.focus_set()
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=30, pady=(4, 16))
        button(row, "Back home", self.home, color=PANEL).pack(side="left")
        last = self.step + 1 == len(steps)
        button(row, "Finish sitting" if last else "Next step", self.next_step,
               color=GOOD if last else BLUE).pack(side="right")
        self.tick()

    def tick(self):
        m, s = divmod(abs(self.left), 60)
        over = self.left < 0
        self.clock.config(text=f"{'+' if over else ''}{m:02d}:{s:02d}", fg="#f0a39b" if over else FG)
        if self.left == 0:
            self.bell()
        self.left -= 1
        self.job = self.after(1000, self.tick)

    def next_step(self):
        text = self.box.get("1.0", "end").strip()
        if text:
            self.notes.append(f"**{self.stage[2][self.step][0]}**\n\n{text}")
        self.step += 1
        if self.step < len(self.stage[2]):
            self.show_step()
            return
        if self.notes:
            append_note(self.title_, self.stage[0], "\n\n".join(self.notes))
        nxt = finish_stage(self.books, self.title_)
        save_json(BOOKS, self.books)
        self.clear()
        tk.Frame(self, bg=BG, height=40).pack()
        if nxt:
            self.label("Sitting done.", 22, GOOD, bold=True)
            self.label(f"Next: {nxt} on {self.books[self.title_]['due']}. Take five quiet minutes away from the "
                       f"screen now. It helps the reading stick.", 13)
        else:
            self.label("Book done.", 22, GOOD, bold=True)
            self.label("Every question answered from memory, checked twice over a month.", 13)
        self.label(f"Your notes: {NOTES / (slug(self.title_) + '.md')}", 10, DIM)
        button(self, "Back home", self.home).pack(pady=20)


if __name__ == "__main__":
    Routine().mainloop()
