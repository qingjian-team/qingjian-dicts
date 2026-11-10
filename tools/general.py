#!/usr/bin/env python3
"""把通用扩展词库的交付稿（数字声调全量，权重是语料原始计数）整理成本仓库 general/words/ 下的使用文件。

    python3 tools/general.py <交付稿.tsv 或按首字母拆开的目录>

规则与输入法仓库 dict-convert `lexicon/general.rs` 的 merge 一致，整理完和基础词库互不重复，打包时不再处理：
- 基础词库（words.tsv + supplement.tsv）已有同词同音（不计声调）的，剔掉；
- 权重换算成基础词库的词频尺度：两边共有的词上拟合 ln(词频+1) = 截距 + 斜率·ln(权重+1)（最小二乘）；
- 基础词库有这个词、但读音不同的，换算后再除以 8（多半是误读，别和正读抢位置）。
基础词库换版本后要重跑一遍，tools/check.py 会查两边有没有重复。
"""

from __future__ import annotations

import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "official/lexicon/zh/base"
GENERAL = ROOT / "official/lexicon/zh/general"
DISPUTED_READING_DIVISOR = 8
TONES = re.compile(r"[1-5]")


def base_entries() -> dict[tuple[str, str], int]:
    """基础词库的（词, 无声调读音）→ 词频。"""
    entries = {}
    for name in ("words.tsv", "supplement.tsv"):
        for line in (BASE / name).read_text("utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            word, reading, frequency = line.split("\t")
            key = (word, TONES.sub("", reading))
            entries[key] = max(entries.get(key, 0), int(frequency))
    return entries


def delivery(source: Path) -> list[tuple[str, str, int]]:
    files = sorted(source.glob("*.tsv")) if source.is_dir() else [source]
    rows = []
    for file in files:
        for line in file.read_text("utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            word, reading, weight = line.split("\t")
            rows.append((word, reading, int(weight)))
    return rows


def fit(pairs: list[tuple[int, int]]) -> tuple[float, float]:
    xs = [math.log(w + 1) for w, _ in pairs]
    ys = [math.log(f + 1) for _, f in pairs]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - slope * mx, slope


def bucket(reading: str) -> str:
    """按拼音首字母拆文件，zh / ch / sh 分别归在 z / c / s。"""
    return reading[0]


def main(args: list[str]) -> int:
    if len(args) != 1:
        print(__doc__)
        return 2
    base = base_entries()
    base_words = {word for word, _ in base}
    rows = delivery(Path(args[0]))
    toneless = [(word, reading, weight, TONES.sub("", reading)) for word, reading, weight in rows]
    pairs = [(weight, base[(word, key)]) for word, _, weight, key in toneless if base.get((word, key), 0) > 0]
    intercept, slope = fit(pairs)

    files: dict[str, list[str]] = defaultdict(list)
    dropped = disputed = 0
    for word, reading, weight, key in toneless:
        if (word, key) in base:
            dropped += 1
            continue
        frequency = max(1, round(math.exp(intercept + slope * math.log(weight + 1)) - 1))
        if word in base_words:
            frequency = max(1, frequency // DISPUTED_READING_DIVISOR)
            disputed += 1
        files[bucket(reading)].append(f"{word}\t{reading}\t{frequency}\n")

    words = GENERAL / "words"
    for old in words.glob("*.tsv"):
        old.unlink()
    for letter, lines in files.items():
        lines.sort(key=lambda line: line.encode("utf-8"))
        (words / f"{letter}.tsv").write_bytes("".join(lines).encode("utf-8"))
    kept = sum(map(len, files.values()))
    print(f"交付稿 {len(rows)} 条：剔掉与基础词库同词同音的 {dropped}，留下 {kept}（其中同词异读 {disputed}）")
    print(f"词频换算：{len(pairs)} 对共有词，斜率 {slope:.3f}，截距 {intercept:.3f}；写了 {len(files)} 个文件：{''.join(sorted(files))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
