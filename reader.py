#!/usr/bin/env python3
"""Speed reader: shows text one word at a time in the same spot, so your eyes don't move.

Paste text or open a .txt / .md file, pick a speed, press Space.
Keys: Space start/pause, Left back one sentence, Right forward one sentence, Up/Down speed, Esc back to text.

Good for light reading and for getting through easy material. For hard material read normally:
comprehension drops when you can't glance back (Rayner et al. 2016). Left is there so you can.
"""
import re



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


if __name__ == "__main__":
    import learning_kit
    learning_kit.main("reader")
