#!/usr/bin/env python3
"""Quiz: multiple-choice questions from a deck file, one at a time, with the reason after each answer.

  python3 quiz.py                  pick a deck from the decks/ folder
  python3 quiz.py decks/my.json    run that deck
  python3 quiz.py --missed         only the questions you got wrong last time, across all decks

Keys: 1-9 pick an answer, Enter check / next. Question order and answer order are shuffled every run.

Deck format (JSON):
  {"title": "My book", "questions": [
     {"q": "Question?", "options": ["right", "wrong", "wrong"], "answer": 0, "why": "Because ... (p. 12)"}]}
"""
import json
import random
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from common import BAD, BG, BLUE, DATA, DIM, FG, FONT, GOOD, HERE, PANEL, button, load_json, save_json

HISTORY = DATA / "quiz-history.json"   # {deck title: {"last": {...}, "missed": [question text, ...]}}


def load_deck(path):
    with open(path, encoding="utf-8") as f:
        deck = json.load(f)
    qs = deck.get("questions", [])
    for i, q in enumerate(qs):
        if not (isinstance(q.get("options"), list) and 0 <= q.get("answer", -1) < len(q["options"])):
            raise ValueError(f"question {i + 1} in {path}: 'answer' must point at one of its 'options'")
        q.setdefault("why", "")
        q["deck"] = deck.get("title", Path(path).stem)
    return deck.get("title", Path(path).stem), qs


def missed_questions(history, decks_dir):
    out = []
    for p in sorted(Path(decks_dir).glob("*.json")):
        title, qs = load_deck(p)
        wrong = set(history.get(title, {}).get("missed", []))
        out += [q for q in qs if q["q"] in wrong]
    return out


def record(history, results):
    """results: [(question dict, right?)]. Stores the score and the missed list per deck."""
    by_deck = {}
    for q, right in results:
        d = by_deck.setdefault(q["deck"], {"score": 0, "total": 0, "missed": []})
        d["total"] += 1
        d["score"] += right
        if not right:
            d["missed"].append(q["q"])
    stamp = time.strftime("%Y-%m-%d %H:%M")
    for deck, d in by_deck.items():
        h = history.setdefault(deck, {})
        old = set(h.get("missed", []))
        asked = {q["q"] for q, _ in results if q["deck"] == deck}
        h["missed"] = sorted((old - asked) | set(d["missed"]))
        h["last"] = {"score": d["score"], "total": d["total"], "date": stamp}
    return history


class Quiz(tk.Tk):
    def __init__(self, title, questions):
        super().__init__()
        self.deck_title, self.all = title, questions
        self.title(f"Quiz: {title}")
        self.geometry("840x620")
        self.configure(bg=BG)
        self.bind("<Key>", self.on_key)
        self.start()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def label(self, text, size=13, color=FG, bold=False):
        l = tk.Label(self, text=text, bg=BG, fg=color, font=(FONT, size, "bold" if bold else "normal"),
                     wraplength=780, justify="left", anchor="w")
        l.pack(fill="x", padx=30, pady=(0, 8))
        return l

    def start(self):
        self.order = random.sample(self.all, len(self.all))
        self.i, self.results, self.finished = 0, [], False
        self.show()

    def show(self):
        self.clear()
        self.answered, self.sel = False, None
        q = self.order[self.i]
        shuffled = random.sample(list(enumerate(q["options"])), len(q["options"]))
        self.opts = [t for _, t in shuffled]
        self.correct = [k for k, _ in shuffled].index(q["answer"])
        score = sum(r for _, r in self.results)
        tk.Frame(self, bg=BG, height=18).pack()
        self.label(f"Question {self.i + 1} of {len(self.order)}   |   {q['deck']}   |   Score {score}", 10, DIM)
        self.label(q["q"], 16, bold=True)
        self.btns = []
        for k, t in enumerate(self.opts):
            b = tk.Button(self, text=f"{k + 1}.  {t}", anchor="w", justify="left", wraplength=740, bg=PANEL, fg=FG,
                          activebackground="#3b4760", activeforeground=FG, relief="flat", font=(FONT, 12),
                          padx=14, pady=8, command=lambda k=k: self.pick(k))
            b.pack(fill="x", padx=30, pady=3)
            self.btns.append(b)
        self.feedback = self.label("", 12)
        self.feedback.pack_configure(pady=(14, 8))
        self.action = button(self, "Check answer (Enter)", self.advance, state="disabled")
        self.action.pack(pady=10)

    def pick(self, k):
        if self.answered:
            return
        self.sel = k
        for j, b in enumerate(self.btns):
            b.config(bg="#4b5d85" if j == k else PANEL)
        self.action.config(state="normal")

    def advance(self):
        if self.sel is None:
            return
        q = self.order[self.i]
        if not self.answered:
            self.answered = True
            right = self.sel == self.correct
            self.results.append((q, right))
            for j, b in enumerate(self.btns):
                b.config(bg=GOOD if j == self.correct else BAD if j == self.sel else PANEL)
            head = "Correct!" if right else f"Not quite. The answer is {self.correct + 1}. {self.opts[self.correct]}"
            self.feedback.config(text=f"{head}\n{q['why']}".strip(), fg=GOOD if right else "#f0a39b")
            self.action.config(text="Next (Enter)" if self.i + 1 < len(self.order) else "See results (Enter)")
        elif self.i + 1 < len(self.order):
            self.i += 1
            self.show()
        else:
            self.done()

    def done(self):
        history = load_json(HISTORY, {})
        prev = history.get(self.deck_title, {}).get("last")
        save_json(HISTORY, record(history, self.results))
        self.clear()
        score = sum(r for _, r in self.results)
        tk.Frame(self, bg=BG, height=20).pack()
        self.label(f"Score: {score} / {len(self.results)}", 24, bold=True)
        if prev:
            self.label(f"Last time: {prev['score']}/{prev['total']} ({prev['date']})", 12, DIM)
        button(self, "Again (Enter)", self.start).pack(pady=(0, 10))
        missed = [q for q, r in self.results if not r]
        if missed:
            self.label("The ones you missed (run with --missed to drill just these):", 12, DIM)
            box = tk.Text(self, bg=BG, fg=FG, font=(FONT, 11), wrap="word", bd=0, highlightthickness=0, height=12)
            box.pack(fill="both", expand=True, padx=30, pady=(0, 16))
            box.insert("1.0", "\n\n".join(f"- {q['q']}\n   {q['options'][q['answer']]}" for q in missed))
            box.config(state="disabled")
        else:
            self.label("Perfect score.", 14, GOOD)
        self.finished = True

    def on_key(self, e):
        if self.finished:
            if e.keysym == "Return":
                self.start()
        elif e.char and e.char.isdigit() and 1 <= int(e.char) <= len(self.opts):
            self.pick(int(e.char) - 1)
        elif e.keysym == "Return":
            self.advance()


def main(args):
    decks = HERE / "decks"
    if "--missed" in args:
        qs = missed_questions(load_json(HISTORY, {}), decks)
        if not qs:
            print("Nothing missed. Run a deck first.")
            return
        Quiz("Missed questions", qs).mainloop()
        return
    path = args[0] if args else None
    if not path:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(initialdir=decks, filetypes=[("Quiz deck", "*.json")])
        root.destroy()
        if not path:
            return
    title, qs = load_deck(path)
    Quiz(title, qs).mainloop()


if __name__ == "__main__":
    main(sys.argv[1:])
