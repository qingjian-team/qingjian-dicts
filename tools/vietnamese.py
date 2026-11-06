#!/usr/bin/env python3
"""从越南语释义表派生越南语输入用的两张表，写进 official/lexicon/vi/ 下的两本：

    python3 tools/vietnamese.py

- words/words.tsv：越南语词表（`词\t词\t次数`），越南语输入法按前缀补全，次数是这个词在释义表里出现的次数；
- chinese/chinese.tsv：越南语 → 中文对照（`词\t中文…`，每词最多两个，按出现次数排），显示在越南语候选旁边。

释义表 official/glossary/vi/glossary.tsv 改了就重跑，两张表跟着提交，变了的那本 version 升一号。
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "official/glossary/vi/glossary.tsv"
OUT = ROOT / "official/lexicon/vi"


def main() -> int:
    words: Counter[str] = Counter()
    chinese: dict[str, Counter[str]] = {}
    with SOURCE.open(encoding="utf-8") as source:
        for line in source:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            source_word = fields[0].strip()
            for field in fields[1:]:
                text = field.split(". ", 1)[-1].split("|", 1)[0].strip().lower()
                if len(text) >= 2 and all(char.isalpha() or char in " -'" for char in text):
                    words[text] += 1
                    chinese.setdefault(text, Counter())[source_word] += 1

    with (OUT / "words/words.tsv").open("w", encoding="utf-8", newline="\n") as output:
        for word, count in sorted(words.items()):
            output.write(f"{word}\t{word}\t{count}\n")

    with (OUT / "chinese/chinese.tsv").open("w", encoding="utf-8", newline="\n") as output:
        for word, senses in sorted(chinese.items()):
            ranked = sorted(senses.items(), key=lambda item: (-item[1], item[0]))[:2]
            output.write(word + "\t" + "\t".join(text for text, _ in ranked) + "\n")

    print(f"words.tsv {len(words)} 条，chinese.tsv {len(chinese)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
