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
import time
from pathlib import Path

from common import DATA

HISTORY = DATA / "quiz-history.json"   # {deck title: {"last": {...}, "missed": [question text, ...]}}


def load_deck(path):
    with open(path, encoding="utf-8") as f:
        deck = json.load(f)
    # A deck is edited by hand: anything malformed is a ValueError naming the question, never a crash.
    if not isinstance(deck, dict) or not isinstance(deck.get("questions", []), list):
        raise ValueError(f"{path}: expected {{\"title\": ..., \"questions\": [...]}}")
    qs = deck.get("questions", [])
    for i, q in enumerate(qs):
        if not isinstance(q, dict) or not isinstance(q.get("q"), str) or not q["q"].strip():
            raise ValueError(f"question {i + 1} in {path}: each question needs its text in \"q\"")
        a = q.get("answer")
        if not (isinstance(q.get("options"), list) and type(a) is int and 0 <= a < len(q["options"])):
            raise ValueError(f"question {i + 1} in {path}: 'answer' must be the number of one of its 'options', "
                             f"counting from 0")
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


if __name__ == "__main__":
    import learning_kit
    learning_kit.main("quiz")
