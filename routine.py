#!/usr/bin/env python3
"""Book routine: get a non-fiction book into your head in three short sittings and two checks.

Add a book, then each day open this and do what's due. One step on screen at a time, each with its own timer.
What you type goes into a Markdown file per book (in ~/.learning-kit/books/), so your answers stay yours.
When you finish a sitting, the next one is scheduled for you.

Why each step is there is in the README, with the studies behind it.
"""
import datetime as dt
import re

from common import DATA, load_json, save_json

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


if __name__ == "__main__":
    import learning_kit
    learning_kit.main("routine")
