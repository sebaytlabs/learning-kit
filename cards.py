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


if __name__ == "__main__":
    import learning_kit
    learning_kit.main("cards")
