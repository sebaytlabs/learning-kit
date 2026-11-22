# Learning Kit

Small tools for reading a book and still remembering it a month later. They're free and work offline, with no account. They run on Windows, Mac and Linux.

| Tool | What it does |
|---|---|
| **Book Routine** | Takes a non-fiction book through three short sittings and two checks, one step at a time with a timer. Your answers go into a Markdown file per book. |
| **Flashcards** | Spaced review from a plain text file (`question :: answer`). Cards you know come back less often. |
| **Quiz** | Multiple choice from a JSON deck, with the reason shown after every answer. Drills the ones you missed. |
| **Speed Reader** | One word at a time in the same spot. Made for light reading. |
| **Typing** | Learn the Colemak keyboard layout on your normal keyboard, with no settings changed. |

## Start

You need Python 3.9 or newer.
- **Windows and Mac:** the installer from [python.org](https://www.python.org/downloads/) includes everything.
- **Linux:** also run `sudo apt install python3-tk` (or your distro's equivalent).

```
git clone https://github.com/sebaytlabs/learning-kit
cd learning-kit
python3 learning_kit.py
```

That opens one window with every tool in a sidebar on the left. Each page opens on a start screen that says what it's for and how to use it, and nothing starts until you press a button. Press **F1** or **Help** on any page for step-by-step help.

Your data lives in `~/.learning-kit/`: book progress, notes, card progress and quiz history. Set `LEARNING_KIT_HOME` to keep it somewhere else, such as a synced folder.

## The book routine

| When | Sitting | Time |
|---|---|---|
| Day 1 | **First look:** purpose, preview, optional skim, trigger words, 3 to 5 questions. Then stop. | ~20 min |
| Day 2 | **Find the answers:** for each question, guess first, find the place, skim, read it properly, write the answer from memory. | ~25 min |
| Day 4 | **Say it back:** two minutes out loud with the book closed, answer every question again, fix, pick one action. | ~20 min |
| Week 2 | **Check:** answer every question from memory. | 5 min |
| Month 1 | **Check:** same again. Then the book is done. | 5 min |

The app shows what's due today, runs a timer for each step and books the next sitting when you finish one.

### Why each step is there

The routine keeps what reading research supports and drops what it doesn't.

- **A purpose first.** Reading toward a stated goal steers what you take in.
- **Preview: how is the book built?** Using a text's structure is one of the larger effects in reading research (Hebert et al. 2016, 45 studies).
- **Questions before reading, and guess before you look.** Questions asked before reading raise what you learn about them, even when your first guess is wrong (Pan & Carpenter 2023). Why and how questions do the most (Bisra et al. 2018, 64 studies).
- **Stop, and come back tomorrow.** A gap between sittings and sleep in between both strengthen memory (Carpenter, Pan & Butler 2022).
- **Write answers from memory.** Recalling is the most effective study method tested (Dunlosky et al. 2013; Yang et al. 2021).
- **Read the answer at normal pace, and go back if you need to.** Taking away re-reading dropped comprehension from 75% to 50% (Rayner et al. 2016).
- **Explain it out loud.** Explaining helps, and out loud beats writing (Lachner et al. 2021).
- **Two spaced checks.** Recalling each answer once in each of three spaced sessions kept 68%, against 26% for three times in one session (Rawson & Dunlosky 2022).
- **No music with words.** Lyrics hurt reading; music without words is about neutral (Vasilev et al. 2018).
- **Five quiet minutes after.** Rest after learning seems to help. Promising, still debated.

### About speed reading

The speed reader is honest about what it's for. Showing words one at a time feels fast, but it takes away the glances back that reading depends on, so comprehension drops on hard material (Rayner et al. 2016). Use it for light reading. **Left** jumps back a sentence whenever you need it.

## Make your own decks and cards

Both can be made inside the app: **New card file** and **Add cards** on the Flashcards page, and **New deck** on the Quiz page. Your own files are kept in `~/.learning-kit/my-cards/` and `~/.learning-kit/my-decks/`. The file formats are below if you'd rather write them by hand.

**Cards:** a `.txt` file, one card per line:

```
What is spaced review? :: Seeing a card again just before you'd forget it
```

**Quiz deck:** a `.json` file:

```json
{"title": "My book", "questions": [
  {"q": "Question?", "options": ["right", "wrong", "wrong"], "answer": 0, "why": "Because ... (p. 12)"}
]}
```

`answer` is the position of the right option, counting from 0. Options are shuffled every run.

## Tests

```
python3 -m unittest discover tests
```

## License

MIT. Made by [Sebayt Labs](https://sebaytlabs.com).
