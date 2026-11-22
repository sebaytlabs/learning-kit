"""Logic tests (no windows).  python3 -m unittest discover tests"""
import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["LEARNING_KIT_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cards  # noqa: E402
import quiz  # noqa: E402
import reader  # noqa: E402
import routine  # noqa: E402

D = dt.date(2026, 1, 1)


class ReaderTest(unittest.TestCase):
    def test_words_strip_markdown(self):
        self.assertEqual(reader.words("# Title\nSome **bold** and [a link](http://x)."),
                         ["Title", "Some", "bold", "and", "a", "link."])

    def test_sentence_end_gets_longer(self):
        self.assertGreater(reader.delay_ms("end.", 300), reader.delay_ms("mid", 300))
        self.assertEqual(reader.delay_ms("mid", 300), 200)

    def test_sentence_starts(self):
        self.assertEqual(reader.sentence_starts("One two. Three! Four".split()), [0, 2, 3])

    def test_focus(self):
        self.assertEqual(reader.focus_index("a"), 0)
        self.assertEqual(reader.focus_index("reading"), 2)


class RoutineTest(unittest.TestCase):
    def test_schedule_runs_to_done(self):
        b = routine.add_book({}, "Book", D)
        self.assertEqual(routine.due_books(b, D), ["Book"])
        self.assertEqual(routine.finish_stage(b, "Book", D), "Find the answers")
        self.assertEqual(b["Book"]["due"], "2026-01-02")
        self.assertEqual(routine.due_books(b, D), [])
        for _ in range(3):
            routine.finish_stage(b, "Book", D)
        self.assertEqual(b["Book"]["due"], "2026-01-24")
        self.assertIsNone(routine.finish_stage(b, "Book", D))
        self.assertIn("done", b["Book"])

    def test_note_file(self):
        p = routine.append_note("A/B: c?", "First look", "hello")
        self.assertTrue(p.read_text().startswith("# A/B: c?"))
        self.assertEqual(p.name, "AB-c.md")


class QuizTest(unittest.TestCase):
    def test_sample_deck_loads(self):
        title, qs = quiz.load_deck(Path(__file__).parent.parent / "decks" / "book-routine.json")
        self.assertTrue(qs and all(q["deck"] == title for q in qs))

    def test_bad_answer_index(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"questions": [{"q": "x", "options": ["a"], "answer": 3}]}, f)
        with self.assertRaises(ValueError):
            quiz.load_deck(f.name)

    def test_missed_list_updates(self):
        q1 = {"q": "one", "deck": "D"}
        q2 = {"q": "two", "deck": "D"}
        h = quiz.record({}, [(q1, False), (q2, True)])
        self.assertEqual(h["D"]["missed"], ["one"])
        h = quiz.record(h, [(q1, True)])
        self.assertEqual(h["D"]["missed"], [])


class CardsTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(cards.parse("# c\nQ :: A :: B\nbad line\n :: x\n"), [("Q", "A :: B")])

    def test_boxes(self):
        p = {}
        cards.grade(p, "q", True, D)
        self.assertEqual(p[cards.key("q")]["due"], "2026-01-03")
        cards.grade(p, "q", True, D)
        self.assertEqual(p[cards.key("q")]["due"], "2026-01-05")
        cards.grade(p, "q", False, D)
        self.assertEqual(p[cards.key("q")], {"box": 0, "due": "2026-01-02"})

    def test_due(self):
        p = {}
        cs = [("a", "1"), ("b", "2")]
        cards.grade(p, "a", True, D)
        self.assertEqual(cards.due(cs, p, D), [("b", "2")])


if __name__ == "__main__":
    unittest.main()
