#!/usr/bin/env python3
"""Learning Kit: one window for reading a book and remembering it.

  python3 learning_kit.py

Pages: Home, Book Routine, Flashcards, Quiz, Speed Reader, Typing. Every page opens on a start screen that says
what it's for and how to use it; nothing starts until you press a button. Press F1 on any page for help.
"""
import datetime as dt
import json
import random
import sys
import time
import tkinter as tk
import tkinter.simpledialog  # noqa: F401  (New card file / New deck)
from pathlib import Path
from tkinter import filedialog, messagebox

import cards
import colemak
import quiz
import reader
import routine
from appkit import BG, DIM, FG, FONT, LINE, PANEL, App, Page, open_path
from common import DATA, HERE, load_json, save_json

ACCENT = "#3b5bdb"
GOOD, BAD = "#2f9e44", "#e03131"
MY_CARDS, MY_DECKS = DATA / "my-cards", DATA / "my-decks"
ABOUT = ("Learning Kit\n\nSmall tools for reading a book and still remembering it a month later.\n"
         "Free and open source (MIT), by Sebayt Labs.\n\nYour books, notes, cards and scores are kept in:\n"
         f"{DATA}")


# ------------------------------------------------------------------ Home
class Home(Page):
    HELP = "Pick a tool on the left, or press Open on one of the cards here. Each tool explains itself when it opens."
    HINT = "Start with Book Routine if you have a book to read."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.title("Read a book. Remember it.",
                   "Five small tools that work together. Start with the Book Routine; it uses the others' ideas.")
        grid = self.grid = tk.Frame(self.body, bg=BG)
        grid.pack(fill="both", expand=True)
        tools = [
            ("routine", "Book Routine", "A non-fiction book in three short sittings and two quick checks. "
                                        "One step at a time, with a timer. Your answers are saved."),
            ("cards", "Flashcards", "Facts you want to keep. Cards you know come back less often; "
                                    "cards you miss come back tomorrow."),
            ("quiz", "Quiz", "Multiple-choice questions on a book, with the reason after every answer."),
            ("reader", "Speed Reader", "Words flash one at a time in the same spot. For light, easy reading."),
            ("typing", "Typing", "Learn the Colemak keyboard layout on the keyboard you already have."),
        ]
        for i, (key, name, what) in enumerate(tools):
            c = tk.Frame(grid, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
            c.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)
            tk.Label(c, text=name, bg=PANEL, fg=FG, font=(FONT, 14, "bold"), anchor="w").pack(fill="x", padx=16,
                                                                                            pady=(12, 2))
            tk.Label(c, text=what, bg=PANEL, fg=DIM, font=(FONT, 11), anchor="w", justify="left",
                     wraplength=360).pack(fill="x", padx=16)
            self.button(c, f"Open {name}", lambda k=key: app.show(k)).pack(anchor="w", padx=16, pady=12)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)


# ------------------------------------------------------------------ Book Routine
class RoutinePage(Page):
    HELP = ("Book Routine\n\n1. Type a book's title at the bottom and press Add book.\n"
            "2. It's due today. Press Start next to it.\n"
            "3. Each step shows what to do and a timer. Type your answers in the box, then press Next step.\n"
            "4. When the sitting ends, the next one is booked for you (tomorrow, 2 days later, a week, a month).\n\n"
            "Your answers are saved as a Markdown file per book. Use 'Open my notes' to see them.")
    HINT = "Add a book at the bottom, then press Start."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.books = load_json(routine.BOOKS, {})
        self.job = None
        self.home()

    def hidden(self):
        pass  # a sitting keeps its timer while you look at another page

    def stop_timer(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None

    def home(self):
        self.stop_timer()
        self.clear()
        self.title("Book Routine", "Get a non-fiction book into your head in about an hour, spread over a month.")
        self.steps(["Add a book you want to learn from (bottom of this page).",
                    "Do today's sitting: one step at a time, each with a timer. Type your answers as you go.",
                    "Come back when the next sitting is due. This page shows what's due.",
                    "After two short checks (a week and a month later), the book is done."])
        due = routine.due_books(self.books)
        self.start_btns = []
        self.text("Due today", 14, bold=True)
        if not due:
            self.text("Nothing due today." + ("" if self.books else " Add your first book below."), 11, DIM)
        for t in due:
            r = self.card()
            stage = routine.STAGES[self.books[t]["stage"]]
            mins = sum(m for _, m, _ in stage[2])
            tk.Label(r, text=t, bg=PANEL, fg=FG, font=(FONT, 12, "bold")).pack(side="left", padx=14, pady=10)
            tk.Label(r, text=f"{stage[0]}  ·  about {mins} min", bg=PANEL, fg=DIM, font=(FONT, 11)).pack(side="left")
            b = self.button(r, "Start", lambda t=t: self.run(t))
            b.pack(side="right", padx=10, pady=6)
            self.start_btns.append((t, b))
        later = sorted((b["due"], t) for t, b in self.books.items() if "due" in b and t not in due)
        if later:
            self.text("Coming up", 12, bold=True, pady=(12, 2))
            for d, t in later[:6]:
                self.text(f"{dt.date.fromisoformat(d):%a %b %d}    {t}  ·  {routine.STAGES[self.books[t]['stage']][0]}",
                          11, DIM, pady=0)
        done = sorted(t for t, b in self.books.items() if "done" in b)
        if done:
            self.text(f"Finished: {', '.join(done)}", 11, GOOD, pady=(10, 0))
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(side="bottom", fill="x", padx=28, pady=16)
        tk.Label(bottom, text="Book title", bg=BG, fg=FG, font=(FONT, 11)).pack(side="left")
        self.entry = tk.Entry(bottom, font=(FONT, 12), relief="solid", bd=1)
        self.entry.pack(side="left", fill="x", expand=True, padx=8, ipady=5)
        self.entry.bind("<Return>", lambda e: self.add())
        self.button(bottom, "Add book", self.add).pack(side="left")
        self.button(bottom, "Open my notes", lambda: (routine.NOTES.mkdir(parents=True, exist_ok=True),
                                                       open_path(routine.NOTES)), primary=False).pack(side="left", padx=8)
        self.bottom = bottom

    def clear(self):
        super().clear()
        if getattr(self, "bottom", None):
            self.bottom.destroy()
            self.bottom = None

    def add(self):
        t = self.entry.get().strip()
        if not t:
            self.app.say("Type a book title first.")
            return
        if t in self.books:
            messagebox.showinfo("Book Routine", f"'{t}' is already on your list.")
            return
        routine.add_book(self.books, t)
        save_json(routine.BOOKS, self.books)
        self.app.say(f"Added '{t}'. Its first sitting is due today.")
        self.home()

    def run(self, title):
        self.book, self.step = title, 0
        self.stage = routine.STAGES[self.books[title]["stage"]]
        self.notes = []
        self.show_step()

    def show_step(self):
        self.stop_timer()
        self.clear()
        name, steps = self.stage[0], self.stage[2]
        step, minutes, what = steps[self.step]
        self.text(f"{self.book}  ·  {name}  ·  step {self.step + 1} of {len(steps)}", 11, DIM)
        bar = tk.Frame(self.body, bg=LINE, height=6)
        bar.pack(fill="x", pady=(0, 12))
        tk.Frame(bar, bg=self.app.accent, height=6).place(relwidth=(self.step + 1) / len(steps), relheight=1)
        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x")
        left = tk.Frame(top, bg=BG)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=step, bg=BG, fg=FG, font=(FONT, 22, "bold"), anchor="w").pack(fill="x")
        tk.Label(left, text=what, bg=BG, fg=FG, font=(FONT, 13), anchor="w", justify="left",
                 wraplength=600).pack(fill="x", pady=6)
        self.clock = tk.Label(top, bg=BG, fg=FG, font=(FONT, 30, "bold"))
        self.clock.pack(side="right", padx=10)
        self.text("Your notes for this step (saved when you press Next):", 10, DIM, pady=(10, 2))
        self.box = tk.Text(self.body, font=(FONT, 12), wrap="word", relief="solid", bd=1, height=8, padx=8, pady=6)
        self.box.pack(fill="both", expand=True)
        self.box.focus_set()
        r = self.row(pady=12)
        self.button(r, "Stop and go back", self.stop_sitting, primary=False).pack(side="left")
        self.step_row = r
        last = self.step + 1 == len(steps)
        self.button(r, "Finish this sitting" if last else "Next step  →", self.next_step).pack(side="right")
        self.left = minutes * 60
        self.app.say(f"Timer: {minutes} min for this step. It beeps at zero and keeps counting; that's fine.")
        self.tick()

    def tick(self):
        m, s = divmod(abs(self.left), 60)
        self.clock.config(text=f"{'+' if self.left < 0 else ''}{m:02d}:{s:02d}", fg=BAD if self.left < 0 else FG)
        if self.left == 0:
            self.bell()
        self.left -= 1
        self.job = self.after(1000, self.tick)

    def stop_sitting(self):
        """Leave a sitting halfway. What you wrote so far is kept in the book's notes; the sitting stays due."""
        text = self.box.get("1.0", "end").strip()
        if text:
            self.notes.append(f"**{self.stage[2][self.step][0]}**\n\n{text}")
        if self.notes:
            routine.append_note(self.book, self.stage[0] + " (stopped early)", "\n\n".join(self.notes))
            self.app.say("Your answers so far are saved in the book's notes. The sitting is still due.")
        self.home()

    def next_step(self):
        text = self.box.get("1.0", "end").strip()
        if text:
            self.notes.append(f"**{self.stage[2][self.step][0]}**\n\n{text}")
        self.step += 1
        if self.step < len(self.stage[2]):
            self.show_step()
            return
        self.stop_timer()
        path = routine.append_note(self.book, self.stage[0], "\n\n".join(self.notes)) if self.notes else None
        nxt = routine.finish_stage(self.books, self.book)
        save_json(routine.BOOKS, self.books)
        self.clear()
        self.title("Sitting done." if nxt else "Book done.")
        if nxt:
            day = dt.date.fromisoformat(self.books[self.book]["due"])
            self.text(f"Next: {nxt}, on {day:%A %B %d}. It will show under Due today.", 13)
            self.text("Now take five quiet minutes away from the screen. It helps the reading stick.", 12, DIM)
        else:
            self.text("Every question answered from memory and checked twice over a month.", 13)
        r = self.row(pady=16)
        self.button(r, "Back to my books", self.home).pack(side="left")
        if path:
            self.button(r, "Open my notes for this book", lambda: open_path(path), primary=False).pack(side="left",
                                                                                                    padx=8)


# ------------------------------------------------------------------ Flashcards
def card_files():
    MY_CARDS.mkdir(parents=True, exist_ok=True)
    return sorted(MY_CARDS.glob("*.txt")) + sorted((HERE / "cards").glob("*.txt"))


class CardsPage(Page):
    HELP = ("Flashcards\n\n1. Make a card file with 'New card file' (or use the example).\n"
            "2. Add cards: type a question and its answer and press Add card.\n"
            "3. Press Review. Say the answer to yourself, press Space to see it, then 1 if you missed it or 2 if you "
            "had it.\n\nCards you know come back after 1, 2, 4, 8, 16, then 32 days. Missed cards come back "
            "tomorrow and once more today.")
    HINT = "Pick a card file, then press Review."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.home()

    def home(self):
        self.unbind_keys()
        self.clear()
        self.title("Flashcards", "Keep facts for good with a few minutes a day. Only the cards that are due show up.")
        self.steps(["Pick a card file below, or make a new one.",
                    "Add cards: a question and its answer.",
                    "Press Review. Answer in your head, press Space, then 1 = missed it, 2 = had it.",
                    "Come back tomorrow. Cards you know show up less and less often."])
        today = dt.date.today()
        self.review_btns = []
        for f in card_files():
            cs = cards.parse(f.read_text(encoding="utf-8"))
            prog = load_json(self.state_file(f), {})
            due = len(cards.due(cs, prog, today))
            r = self.card()
            tk.Label(r, text=f.stem.replace("-", " ").capitalize(), bg=PANEL, fg=FG, font=(FONT, 12, "bold")).pack(
                side="left", padx=14, pady=10)
            tk.Label(r, text=f"{len(cs)} cards  ·  {due} due today", bg=PANEL, fg=GOOD if due else DIM,
                     font=(FONT, 11)).pack(side="left")
            b = self.button(r, "Review", lambda f=f: self.review(f), state="normal" if due else "disabled")
            b.pack(side="right", padx=(4, 10), pady=6)
            self.review_btns.append((f, b))
            self.button(r, "Add cards", lambda f=f: self.adder(f), primary=False).pack(side="right", padx=4)
            self.button(r, "Edit file", lambda f=f: open_path(f), primary=False).pack(side="right", padx=4)
        self.button(self.row(pady=10), "+  New card file", self.new_file, primary=False).pack(side="left")

    def hidden(self):
        self.unbind_keys()
        self.home()

    def state_file(self, f):
        return DATA / "cards" / f"{f.stem}-{cards.key(str(f.resolve()))}.json"

    def new_file(self):
        name = tk.simpledialog.askstring("New card file", "What are these cards about?", parent=self)
        if not name:
            return
        f = MY_CARDS / (routine.slug(name) + ".txt")
        if not f.exists():
            f.write_text(f"# {name}\n# One card per line:  question :: answer\n", encoding="utf-8")
        self.adder(f)

    def adder(self, f):
        self.clear()
        self.title(f"Add cards: {f.stem.replace('-', ' ')}",
                   "Type a question and its answer. Press Enter in the answer box to add it and start the next one.")
        q, a = tk.StringVar(), tk.StringVar()
        for label, var in (("Question", q), ("Answer", a)):
            r = self.row()
            tk.Label(r, text=label, bg=BG, fg=FG, font=(FONT, 12), width=10, anchor="w").pack(side="left")
            e = tk.Entry(r, textvariable=var, font=(FONT, 13), relief="solid", bd=1)
            e.pack(side="left", fill="x", expand=True, ipady=5)
            if label == "Question":
                first = e
            else:
                e.bind("<Return>", lambda ev: add())
        added = self.text("", 11, GOOD)

        def add():
            if not (q.get().strip() and a.get().strip()):
                self.app.say("Both a question and an answer, please.")
                return
            with open(f, "a", encoding="utf-8") as fh:
                fh.write(f"{q.get().strip().replace('::', ':')} :: {a.get().strip()}\n")
            added.config(text=f"Added: {q.get().strip()}")
            q.set("")
            a.set("")
            first.focus_set()
        r = self.row(pady=12)
        self.button(r, "Add card", add).pack(side="left")
        self.button(r, "Done", self.home, primary=False).pack(side="left", padx=8)
        first.focus_set()

    def review(self, f):
        self.file = f
        self.cards = cards.parse(f.read_text(encoding="utf-8"))
        self.progress = load_json(self.state_file(f), {})
        self.queue = cards.due(self.cards, self.progress, dt.date.today())
        random.shuffle(self.queue)
        self.retry, self.count, self.missed = set(), 0, 0
        self.app.bind("<space>", lambda e: self.reveal())
        self.app.bind("1", lambda e: self.answer(False))
        self.app.bind("2", lambda e: self.answer(True))
        self.show_card()

    def unbind_keys(self):
        for k in ("<space>", "1", "2"):
            self.app.unbind(k)

    def show_card(self):
        self.clear()
        self.revealed = False
        if not self.queue:
            self.unbind_keys()
            self.title("All caught up.", f"Reviewed {self.count}, missed {self.missed}. Come back tomorrow.")
            self.button(self.row(), "Back to card files", self.home).pack(side="left")
            return
        self.text(f"{len(self.queue)} left today  ·  {self.file.stem.replace('-', ' ')}", 11, DIM)
        c = self.card(pady=20)
        tk.Label(c, text=self.queue[0][0], bg=PANEL, fg=FG, font=(FONT, 20, "bold"), wraplength=700).pack(pady=(40, 10))
        self.ans = tk.Label(c, text="", bg=PANEL, fg=ACCENT, font=(FONT, 17), wraplength=700)
        self.ans.pack(pady=(0, 40))
        self.r = self.row(pady=10)
        self.button(self.r, "Show answer  (Space)", self.reveal).pack()
        self.button(self.row(pady=20), "Stop for today", self.home, primary=False).pack(side="left")
        self.app.say("Say the answer to yourself first, then press Space.")

    def reveal(self):
        if self.revealed or not self.queue:
            return
        self.revealed = True
        self.ans.config(text=self.queue[0][1])
        for w in self.r.winfo_children():
            w.destroy()
        tk.Button(self.r, text="1   Missed it", command=lambda: self.answer(False), bg=BAD, fg="white", relief="flat",
                  font=(FONT, 12, "bold"), padx=18, pady=8).pack(side="left", padx=8)
        tk.Button(self.r, text="2   Had it", command=lambda: self.answer(True), bg=GOOD, fg="white", relief="flat",
                  font=(FONT, 12, "bold"), padx=18, pady=8).pack(side="left", padx=8)
        self.app.say("Be honest: 1 if you missed it, 2 if you had it.")

    def answer(self, got):
        if not self.revealed:
            return
        q, a = self.queue.pop(0)
        if q not in self.retry:
            cards.grade(self.progress, q, got, dt.date.today())
            save_json(self.state_file(self.file), self.progress)
            self.count += 1
            self.missed += not got
        if not got:
            self.retry.add(q)
            self.queue.append((q, a))
        self.show_card()


# ------------------------------------------------------------------ Quiz
def deck_files():
    MY_DECKS.mkdir(parents=True, exist_ok=True)
    return sorted(MY_DECKS.glob("*.json")) + sorted((HERE / "decks").glob("*.json"))


DECK_TEMPLATE = {"title": "My book", "questions": [
    {"q": "Write the question here?", "options": ["The right answer", "A wrong answer", "Another wrong answer"],
     "answer": 0, "why": "Why it's right, and the page it's on."}]}


class QuizPage(Page):
    HELP = ("Quiz\n\n1. Pick a deck and press Start.\n2. Click an answer (or press 1-4), then Check.\n"
            "3. You see the right answer and why. Press Next.\n4. At the end, 'Missed questions' drills only the ones "
            "you got wrong.\n\nMake your own deck with 'New deck': it opens a file you fill in. Answers are "
            "shuffled every time, so you can't learn the positions.")
    HINT = "Pick a deck and press Start."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.home()

    def home(self):
        self.app.unbind("<Key>")
        self.clear()
        self.title("Quiz", "Test yourself on a book. Every answer shows why it's right.")
        self.steps(["Pick a deck below and press Start.",
                    "Choose an answer, press Check, read why.",
                    "At the end, drill just the ones you missed."])
        hist = load_json(quiz.HISTORY, {})
        self.start_btns = []
        for f in deck_files():
            try:
                title, qs = quiz.load_deck(f)
            except (ValueError, OSError) as e:
                self.text(f"{f.name}: can't read it ({e})", 11, BAD)
                continue
            h = hist.get(title, {})
            last = h.get("last")
            r = self.card()
            tk.Label(r, text=title, bg=PANEL, fg=FG, font=(FONT, 12, "bold")).pack(side="left", padx=14, pady=10)
            info = f"{len(qs)} questions" + (f"  ·  last score {last['score']}/{last['total']}" if last else "")
            tk.Label(r, text=info, bg=PANEL, fg=DIM, font=(FONT, 11)).pack(side="left")
            b = self.button(r, "Start", lambda t=title, q=qs: self.start(t, q))
            b.pack(side="right", padx=(4, 10), pady=6)
            self.start_btns.append(b)
            wrong = [q for q in qs if q["q"] in set(h.get("missed", []))]
            if wrong:
                self.button(r, f"Missed questions ({len(wrong)})", lambda t=title, q=wrong: self.start(t, q),
                            primary=False).pack(side="right", padx=4)
            if f.parent == MY_DECKS:
                self.button(r, "Edit", lambda f=f: open_path(f), primary=False).pack(side="right", padx=4)
        self.button(self.row(pady=10), "+  New deck", self.new_deck, primary=False).pack(side="left")

    def hidden(self):
        self.app.unbind("<Key>")
        self.home()

    def new_deck(self):
        name = tk.simpledialog.askstring("New deck", "Which book is this deck for?", parent=self)
        if not name:
            return
        f = MY_DECKS / (routine.slug(name) + ".json")
        if not f.exists():
            d = json.loads(json.dumps(DECK_TEMPLATE))
            d["title"] = name
            f.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        open_path(f)
        messagebox.showinfo("New deck", f"The deck file is open in your text editor:\n{f}\n\n"
                                        "Copy the example question for each new one. 'answer' is the position of the "
                                        "right option, counting from 0. Save it, then come back here.")
        self.home()

    def start(self, title, qs):
        self.deck_title = title
        self.order = random.sample(qs, len(qs))
        self.i, self.results = 0, []
        self.app.bind("<Key>", self.key)
        self.show()

    def show(self):
        self.clear()
        self.answered, self.sel = False, None
        q = self.order[self.i]
        sh = random.sample(list(enumerate(q["options"])), len(q["options"]))
        self.opts = [t for _, t in sh]
        self.correct = [k for k, _ in sh].index(q["answer"])
        score = sum(r for _, r in self.results)
        self.text(f"Question {self.i + 1} of {len(self.order)}  ·  score {score}", 11, DIM)
        self.text(q["q"], 17, bold=True, pady=(0, 12))
        self.btns = []
        self.choices = tk.Frame(self.body, bg=BG)
        self.choices.pack(fill="x")
        for k, t in enumerate(self.opts):
            b = tk.Button(self.choices, text=f"  {k + 1}.  {t}", anchor="w", justify="left", wraplength=720, bg=PANEL,
                          fg=FG, relief="solid", bd=1, font=(FONT, 12), padx=10, pady=8, cursor="hand2",
                          command=lambda k=k: self.pick(k))
            b.pack(fill="x", pady=3)
            self.btns.append(b)
        self.fb = self.text("", 12, pady=(10, 4))
        r = self.row(pady=8)
        self.button(r, "Quit quiz", self.home, primary=False).pack(side="left")
        self.act = self.button(r, "Check answer", self.advance, state="disabled")
        self.act.pack(side="right")
        self.app.say("Click an answer or press its number, then Check (Enter).")

    def pick(self, k):
        if self.answered:
            return
        self.sel = k
        for j, b in enumerate(self.btns):
            b.config(bg="#dbe4ff" if j == k else PANEL)
        self.act.config(state="normal")

    def advance(self):
        if self.sel is None:
            return
        q = self.order[self.i]
        if not self.answered:
            self.answered = True
            right = self.sel == self.correct
            self.results.append((q, right))
            for j, b in enumerate(self.btns):
                b.config(bg="#d3f9d8" if j == self.correct else "#ffe3e3" if j == self.sel else PANEL)
            head = "Right." if right else f"Not quite. The answer is {self.correct + 1}."
            self.fb.config(text=f"{head}  {q['why']}".strip(), fg=GOOD if right else BAD)
            self.act.config(text="Next question  →" if self.i + 1 < len(self.order) else "See my score")
        elif self.i + 1 < len(self.order):
            self.i += 1
            self.show()
        else:
            self.done()

    def done(self):
        self.app.unbind("<Key>")
        save_json(quiz.HISTORY, quiz.record(load_json(quiz.HISTORY, {}), self.results))
        score = sum(r for _, r in self.results)
        self.clear()
        self.title(f"Score: {score} of {len(self.results)}")
        missed = [q for q, r in self.results if not r]
        if missed:
            self.text("The ones you missed:", 12, DIM)
            for q in missed:
                self.text(f"•  {q['q']}\n    {q['options'][q['answer']]}", 11, pady=(0, 6))
        else:
            self.text("A perfect score.", 13, GOOD)
        r = self.row(pady=14)
        self.button(r, "Back to decks", self.home).pack(side="left")
        if missed:
            self.button(r, "Drill the missed ones", lambda: self.start(self.deck_title, missed),
                        primary=False).pack(side="left", padx=8)

    def key(self, e):
        if e.char and e.char.isdigit() and 1 <= int(e.char) <= len(getattr(self, "opts", [])):
            self.pick(int(e.char) - 1)
        elif e.keysym == "Return":
            self.advance()


# ------------------------------------------------------------------ Speed Reader
SAMPLE = ("Paste any text here, or open a file. This is a sample so you can try it. The words will flash one at a "
          "time in the same spot, so your eyes don't have to move along the line. Press Space to pause. Press the "
          "left arrow to go back a sentence whenever you lose the thread. Start slow, around 250 words a minute, "
          "and speed up once it feels easy. For hard material, read normally: being able to look back matters "
          "more than speed.")


class ReaderPage(Page):
    HELP = ("Speed Reader\n\n1. Paste text into the box or press Open a file (.txt or .md).\n"
            "2. Set the speed. 250 is a comfortable start.\n3. Press Start reading.\n\n"
            "While reading: Space pauses, Left goes back a sentence, Right skips ahead, Up/Down change speed, "
            "Esc stops.\n\nUse it for light reading. On hard material you understand less when you can't glance "
            "back, so read those normally.")
    HINT = "Paste text or open a file, then press Start reading."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.wpm = tk.IntVar(value=250)
        self.job = None
        self.home()

    def home(self, text=None):
        self.stop()
        self.clear()
        self.title("Speed Reader", "Words flash one at a time in the same spot. Good for light reading.")
        self.steps(["Paste text below, or open a .txt or .md file.",
                    "Pick a speed (250 is comfortable to start).",
                    "Press Start reading. Space pauses, Left goes back a sentence, Esc stops."])
        self.box = tk.Text(self.body, font=(FONT, 12), wrap="word", relief="solid", bd=1, height=9, padx=8, pady=6)
        self.box.pack(fill="both", expand=True)
        self.box.insert("1.0", text or SAMPLE)
        r = self.row(pady=10)
        self.button(r, "Open a file…", self.open_file, primary=False).pack(side="left")
        self.button(r, "Clear", lambda: self.box.delete("1.0", "end"), primary=False).pack(side="left", padx=6)
        tk.Label(r, text="   Words a minute", bg=BG, fg=FG, font=(FONT, 11)).pack(side="left")
        tk.Scale(r, from_=100, to=900, resolution=25, orient="horizontal", variable=self.wpm, length=220, bg=BG,
                 highlightthickness=0).pack(side="left", padx=6)
        self.start_b = self.button(r, "Start reading  ▶", self.start)
        self.start_b.pack(side="right")

    def hidden(self):
        if hasattr(self, "canvas") and self.canvas.winfo_exists():
            self.home(self.source)

    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("Text", "*.txt *.md"), ("All files", "*")])
        if p:
            self.box.delete("1.0", "end")
            self.box.insert("1.0", Path(p).read_text(encoding="utf-8", errors="replace"))

    def start(self):
        self.source = self.box.get("1.0", "end")
        self.ws = reader.words(self.source)
        if not self.ws:
            self.app.say("There's no text to read yet.")
            return
        self.starts = reader.sentence_starts(self.ws)
        self.clear()
        self.status = self.text("", 11, DIM)
        self.canvas = tk.Canvas(self.body, bg=PANEL, highlightthickness=1, highlightbackground=LINE, height=220)
        self.canvas.pack(fill="x", pady=10)
        r = self.row()
        self.pause_btn = self.button(r, "Pause  (Space)", self.toggle)
        self.pause_btn.pack(side="left")
        self.button(r, "◀ Back a sentence", lambda: self.jump(-1), primary=False).pack(side="left", padx=6)
        self.button(r, "Ahead ▶", lambda: self.jump(1), primary=False).pack(side="left")
        self.button(r, "Stop  (Esc)", lambda: self.home(self.source), primary=False).pack(side="right")
        for k, fn in (("<space>", lambda e: self.toggle()), ("<Left>", lambda e: self.jump(-1)),
                      ("<Right>", lambda e: self.jump(1)), ("<Up>", lambda e: self.speed(25)),
                      ("<Down>", lambda e: self.speed(-25)), ("<Escape>", lambda e: self.home(self.source))):
            self.app.bind(k, fn)
        self.i, self.paused = 0, False
        self.app.say("Space pauses. Left goes back a sentence. Up and Down change the speed. Esc stops.")
        self.job = self.after(600, self.tick)

    def stop(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        for k in ("<space>", "<Left>", "<Right>", "<Up>", "<Down>", "<Escape>"):
            self.app.unbind(k)

    def draw(self):
        c = self.canvas
        c.delete("all")
        w = self.ws[self.i]
        k = reader.focus_index(w)
        cx, cy = max(c.winfo_width(), 600) // 2, 110
        font = (FONT, 40)
        left = c.create_text(0, cy, text=w[:k], font=font, anchor="e", fill=FG)
        mid = c.create_text(0, cy, text=w[k:k + 1], font=font, anchor="w", fill=BAD)
        right = c.create_text(0, cy, text=w[k + 1:], font=font, anchor="w", fill=FG)
        box = c.bbox(mid)
        mw = (box[2] - box[0]) if box and w[k:k + 1] else 0
        c.coords(left, cx - mw / 2, cy)
        c.coords(mid, cx - mw / 2, cy)
        c.coords(right, cx + mw / 2, cy)
        c.create_line(cx, cy - 50, cx, cy - 36, fill=DIM, width=2)
        c.create_line(cx, cy + 36, cx, cy + 50, fill=DIM, width=2)
        left_min = (len(self.ws) - self.i) / self.wpm.get()
        self.status.config(text=f"{self.wpm.get()} words a minute   ·   word {self.i + 1} of {len(self.ws)}   ·   "
                                f"about {left_min:.0f} min left" + ("   ·   PAUSED" if self.paused else ""))

    def tick(self):
        self.job = None
        if self.paused:
            return
        self.draw()
        if self.i + 1 < len(self.ws):
            delay = reader.delay_ms(self.ws[self.i], self.wpm.get())
            self.i += 1
            self.job = self.after(delay, self.tick)
        else:
            self.paused = True
            self.pause_btn.config(text="Read again")
            self.app.say("Done. Press Read again, or Stop to go back to the text.")

    def toggle(self):
        if self.paused and self.i + 1 >= len(self.ws):
            self.i = 0
        self.paused = not self.paused
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        self.pause_btn.config(text="Resume  (Space)" if self.paused else "Pause  (Space)")
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


# ------------------------------------------------------------------ Typing
class TypingPage(Page):
    HELP = ("Typing: learn Colemak\n\nColemak is a keyboard layout that puts the most used letters under your "
            "fingers, so your hands move less than on QWERTY.\n\nYou don't change any settings: type on your normal "
            "keyboard and this page reads each key as its Colemak letter. The picture shows where each letter is.\n\n"
            "1. Pick lesson 1 and press Start.\n2. Type the line shown. The blue letter is the next one; red means "
            "you pressed the wrong key.\n3. Move to the next lesson when you're above 95% accuracy.")
    HINT = "Pick a lesson and press Start."

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.home()

    def home(self):
        self.app.unbind("<Key>")
        self.clear()
        self.title("Typing: learn Colemak",
                   "Colemak puts the most used letters under your fingers. Learn it here without changing any settings: "
                   "type on your normal keyboard and each key is read as its Colemak letter.")
        self.steps(["Pick a lesson. Lesson 1 is the home row only.",
                    "Type the line. The blue letter is next; red means a wrong key.",
                    "Move on once your accuracy stays above 95%."])
        self.start_btns = []
        for i, (name, letters) in enumerate(colemak.LESSONS):
            r = self.card()
            tk.Label(r, text=f"Lesson {i + 1}: {name}", bg=PANEL, fg=FG, font=(FONT, 12, "bold")).pack(
                side="left", padx=14, pady=10)
            tk.Label(r, text="letters: " + " ".join(letters), bg=PANEL, fg=DIM, font=("Monospace", 11)).pack(side="left")
            b = self.button(r, "Start", lambda i=i: self.start(i))
            b.pack(side="right", padx=10, pady=6)
            self.start_btns.append(b)

    def hidden(self):
        self.home()

    def start(self, lesson):
        self.S = dict(lesson=lesson, text=colemak.lesson_words(lesson), pos=0, bad=False, start=0, chars=0, total=0,
                      errors=0)
        self.clear()
        self.text(f"Lesson {lesson + 1}: {colemak.LESSONS[lesson][0]}", 14, bold=True)
        self.stats = self.text("", 12, DIM)
        self.line = tk.Text(self.body, height=2, font=("Monospace", 26), wrap="word", bg=PANEL, relief="solid", bd=1,
                            padx=12, pady=10, cursor="arrow")
        self.line.tag_config("done", foreground=GOOD)
        self.line.tag_config("cur", background="#bac8ff")
        self.line.tag_config("bad", background="#ffc9c9")
        self.line.pack(fill="x", pady=10)
        self.kb = tk.Canvas(self.body, width=690, height=200, bg=BG, highlightthickness=0)
        self.kb.pack()
        self.text("Big letter = Colemak. Small letter = the key printed on your keyboard. "
                  "Underlined = where your index fingers rest.", 10, DIM)
        r = self.row()
        self.button(r, "Back to lessons", self.home, primary=False).pack(side="left")
        self.app.bind("<Key>", self.key)
        self.app.say("Just start typing.")
        self.render()

    def render(self):
        S = self.S
        letters, text, pos = colemak.LESSONS[S["lesson"]][1], S["text"], S["pos"]
        mins = (time.time() - S["start"]) / 60 if S["start"] else 0
        wpm = round(S["chars"] / 5 / mins) if mins else 0
        acc = round(100 * (S["total"] - S["errors"]) / S["total"]) if S["total"] else 100
        self.stats.config(text=f"Speed {wpm} words a minute    Accuracy {acc}%")
        self.line.config(state="normal")
        self.line.delete("1.0", "end")
        self.line.insert("1.0", text[:pos], "done", text[pos], "bad" if S["bad"] else "cur", text[pos + 1:])
        self.line.config(state="disabled")
        kb = self.kb
        kb.delete("all")
        for r, row in enumerate(colemak.ROWS):
            for j, q in enumerate(row):
                c, x, y = colemak.TO_CM[q], 10 + r * 25 + j * 64, 5 + r * 64
                kb.create_rectangle(x, y, x + 58, y + 58, fill="#bac8ff" if c == text[pos] else PANEL, outline=LINE)
                kb.create_text(x + 29, y + 24, text=c, fill=FG if c in letters else "#adb5bd", font=(FONT, 20))
                kb.create_text(x + 29, y + 47, text=q.upper(), fill=DIM, font=(FONT, 9))
                if c in "tn":
                    kb.create_line(x + 20, y + 55, x + 38, y + 55, fill=FG, width=2)

    def key(self, e):
        k = (e.char or "").lower()
        ch = " " if k == " " else colemak.TO_CM.get(k)
        if not ch:
            return
        S = self.S
        S["start"] = S["start"] or time.time()
        S["total"] += 1
        if ch == S["text"][S["pos"]]:
            S.update(pos=S["pos"] + 1, chars=S["chars"] + 1, bad=False)
            if S["pos"] == len(S["text"]):
                S.update(text=colemak.lesson_words(S["lesson"]), pos=0)
        else:
            S.update(errors=S["errors"] + 1, bad=True)
        self.render()


def alive(w):
    try:
        return w is not None and bool(w.winfo_exists())
    except tk.TclError:
        return False


def tutorial(app):
    pg = app.page
    first = lambda xs: xs[0][1] if xs and isinstance(xs[0], tuple) else (xs[0] if xs else None)
    in_sitting = lambda: alive(getattr(pg("routine"), "clock", None))
    return [
        {"title": "Welcome to Learning Kit", "target": lambda: app.tour_button,
         "text": "Learning Kit is for reading a non-fiction book and still remembering it a month later. This "
                 "tutorial walks through every tool. At each step you do one real thing. It takes about five "
                 "minutes.",
         "do": "read this, then click Next. The Tutorial button runs it again any time."},
        {"title": "Five tools, one idea", "page": "home", "target": lambda: pg("home").grid,
         "text": "Remembering comes from pulling an idea back out of your head, spaced over days. Reading it again "
                 "doesn't do it. The Book Routine does that for a whole book. Flashcards and Quiz do it for single "
                 "facts. The Speed Reader is for light reading. Typing is a bonus: learn a faster keyboard layout.",
         "do": "click Next."},
        {"title": "Book Routine: add a book", "page": "routine", "target": lambda: pg("routine").bottom,
         "text": "Start with a non-fiction book you actually want to learn from. The routine spreads it over five "
                 "short sessions: day 1, day 2, day 4, then checks after a week and a month.",
         "do": "type the title of a book you're reading (or any title to practice), then click Add book.",
         "start": lambda: len(pg("routine").books), "check": lambda n: len(pg("routine").books) > n},
        {"title": "Start today's sitting", "page": "routine",
         "target": lambda: (pg("routine").start_btns or [(None, None)])[-1][1],
         "text": "A new book's first sitting is due today. It takes about 20 minutes, one step at a time.",
         "do": "click Start next to your book.", "check": lambda _: in_sitting()},
        {"title": "One step at a time", "target": lambda: pg("routine").box,
         "text": "The top says what to do and the clock gives you a time limit, so you don't slide into reading the "
                 "whole book. Type your answers in this box. They go into a notes file for the book.",
         "do": "type one line, for example why you're reading this book.",
         "check": lambda _: in_sitting() and pg("routine").box.get("1.0", "end").strip() != ""},
        {"title": "Next step, or stop for now", "target": lambda: pg("routine").step_row,
         "text": "'Next step' saves your answer and moves on. When the sitting is done, the next one is booked for "
                 "you. 'Stop and go back' keeps what you wrote, and the sitting stays due today.",
         "do": "click Stop and go back for now. You'll do the real sitting after the tutorial.",
         "check": lambda _: not in_sitting()},
        {"title": "Flashcards", "page": "cards", "target": lambda: first(pg("cards").review_btns),
         "text": "For facts you want to keep, like a name, a date or a formula. A card file is plain text, one "
                 "'question :: answer' per line. Only the cards that are due show up.",
         "do": "click Review on the first card file.",
         "check": lambda _: alive(getattr(pg("cards"), "ans", None))},
        {"title": "Answer in your head first", "target": lambda: pg("cards").r,
         "text": "Say the answer to yourself, then press Space to see it. Then be honest: 1 if you missed it, 2 if "
                 "you had it. A card you know comes back in 1, 2, 4, 8, 16, then 32 days. One you miss comes back "
                 "today and again tomorrow.",
         "do": "press Space, then 1 or 2.",
         "start": lambda: getattr(pg("cards"), "count", 0),
         "check": lambda n: getattr(pg("cards"), "count", 0) > n},
        {"title": "Quiz", "page": "quiz", "target": lambda: first(pg("quiz").start_btns),
         "text": "Multiple choice on a book, with the reason after every answer. At the end you can drill just the "
                 "ones you missed. The deck here quizzes you on why the Book Routine works the way it does.",
         "do": "click Start.", "check": lambda _: alive(getattr(pg("quiz"), "choices", None))},
        {"title": "Pick, check, read why", "target": lambda: pg("quiz").choices,
         "text": "The options are shuffled every time, so you can't learn the positions.",
         "do": "click an answer (or press its number), then Check answer.",
         "check": lambda _: getattr(pg("quiz"), "answered", False)},
        {"title": "Speed Reader", "page": "reader", "target": lambda: pg("reader").start_b,
         "text": "Words flash one at a time in the same spot. It feels fast, but you can't glance back, and on hard "
                 "text that costs you understanding. So use it for light reading only. Left arrow jumps back a "
                 "sentence and Space pauses.",
         "do": "click Start reading, watch a few words, then press Esc.",
         "check": lambda _: alive(getattr(pg("reader"), "canvas", None))},
        {"title": "Typing: Colemak", "page": "typing", "target": lambda: first(pg("typing").start_btns),
         "text": "Colemak is a keyboard layout that keeps your most used letters under your fingers. You learn it "
                 "here without changing any settings: each key you press is read as its Colemak letter.",
         "do": "click Start on lesson 1.", "check": lambda _: alive(getattr(pg("typing"), "line", None))},
        {"title": "Just type", "target": lambda: pg("typing").line,
         "text": "Blue is the next letter. Red means a wrong key. The keyboard picture shows where each letter is.",
         "do": "type five letters.", "check": lambda _: getattr(pg("typing"), "S", {}).get("total", 0) >= 5},
        {"title": "You're ready", "page": "routine", "target": lambda: app.tour_button,
         "text": "Your book is waiting under Due today. Do its first sitting now or later today, and come back "
                 "when the page says the next one is due. That's the whole habit.\n\nF1 on any page shows help "
                 "for that page.",
         "do": "click Done."},
    ]


def main(first="home"):
    app = App("Learning Kit", "Read a book. Remember it.", ACCENT, ABOUT, class_name="LearningKit")
    app.add_page("home", "Home", Home)
    app.add_page("routine", "Book Routine", RoutinePage)
    app.add_page("cards", "Flashcards", CardsPage)
    app.add_page("quiz", "Quiz", QuizPage)
    app.add_page("reader", "Speed Reader", ReaderPage)
    app.add_page("typing", "Typing", TypingPage)
    icon = HERE / "icon.png"
    if icon.exists():
        app.iconphoto(True, tk.PhotoImage(file=str(icon)))
    app.set_tutorial(lambda: tutorial(app), DATA / "settings.json")
    app.run(first)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "home")
