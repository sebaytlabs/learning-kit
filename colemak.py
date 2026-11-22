#!/usr/bin/env python3
"""Colemak typing trainer. Type on your normal QWERTY keyboard; each key is read as its Colemak letter,
so you can learn the layout without changing any system settings.

Five lessons add letters a few at a time, starting from the home row. Keys 1-5 switch lessons.
"""

QW = "qwertyuiopasdfghjkl;zxcvbnm"
CM = "qwfpgjluy;arstdhneiozxcvbkm"
TO_CM = dict(zip(QW, CM))
ROWS = ["qwertyuiop", "asdfghjkl;", "zxcvbnm"]

LESSONS = [("Home row", "arstneio"), ("+ d h", "arstneiodh"), ("+ f p l u", "arstneiodhfplu"),
           ("+ g j y w q", "arstneiodhfplugjywq"), ("All letters", "arstneiodhfplugjywqcvbkmxz")]
WORDS = """the and for are but not you all any can had her was one our out day get has him his how man new
now old see two way who boy did its let put say she too use that with have this will your from they know
want been good much some time very when come here just like long make many more only over such take than
them well were rest tree near tone seat rain star note stone train tire site iron onion toast straw rose
nose arts eats oats sister senior retain orient snore tennis inert noise into sea ten tea set sit eat ate
air art rat ran nor son sort store stair trait rent tent toe tie those then three heat hand dish shed third
drain other their these there said told need road hint hid hide dirt dear head horse north shoe share dose
idea fold full play plus fluid apple until pure plan pill lift loud soup flour help half path pupil quiet
joy gift yellow world quick jump young why whip query gray weight glow judge fox lazy brown back move voice
cake zone box black mix work vex kick make big cozy maze""".split()



def lesson_words(lesson, n=8, rng=None):
    """A line of n real words using only the letters this lesson has taught."""
    import random as r
    rng = rng or r
    pool = [w for w in WORDS if set(w) <= set(LESSONS[lesson][1])]
    return " ".join(rng.choice(pool) for _ in range(n))


if __name__ == "__main__":
    import learning_kit
    learning_kit.main("typing")
