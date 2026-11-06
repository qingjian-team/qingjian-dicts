#!/usr/bin/env python3
"""发版 workflow 调的：找出 dict.toml 里的版本还没发 Release 的词库，逐本打包并写好 Release 的标题与说明。

    python3 tools/release.py            # 打包到 dist/，每本写 dist/<标签>.md（说明）与 dist/<标签>.title（标题）
    python3 tools/release.py --list     # 只列出要发的标签

已经发过的标签用 gh 查（要 GH_TOKEN 或本机 gh 已登录）。要发的标签一行一个写到标准输出最后，
在 Actions 里另写进 $GITHUB_OUTPUT 的 tags（空格隔开）。不改 index.json：workflow 建完 Release 再调 index.py。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import index  # noqa: E402
import pack  # noqa: E402


def released_tags() -> set[str]:
    out = subprocess.run(
        ["gh", "release", "list", "--limit", "1000", "--json", "tagName"],
        cwd=pack.ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return {entry["tagName"] for entry in json.loads(out)}


def pending() -> list[tuple[str, Path, dict]]:
    done = released_tags()
    found = []
    for section in index.SECTIONS:
        for path in sorted((index.ROOT / section).rglob("dict.toml")):
            meta = tomllib.loads(path.read_text("utf-8"))
            tag = f"{meta['id']}-v{meta['version']}"
            if tag not in done:
                found.append((tag, path.parent, meta))
    return found


def notes(meta: dict) -> str:
    who = "、".join([meta["author"]["name"], *meta.get("credits", [])])
    lines = [meta["description"], "", f"许可 {meta['license']}，署名：{who}。"]
    if meta.get("machine_generated"):
        lines.append(f"{meta['machine_generated']}。")
    lines.append("")
    if meta.get("bundled"):
        lines.append("随青简安装，不用单独下载。")
    elif meta["kind"] == "glossary":
        lines.append("青简「设置 → 词库 → 下载 → 释义表」里安装。")
    else:
        lines.append(f"青简「设置 → 词库 → 下载」里安装，或者下载 `{meta['id']}.qjz` 后在「词库」→「导入」里选它。")
    lines.append("SHA-256 见 `manifest.json`。")
    return "\n".join(lines) + "\n"


def main(args: list[str]) -> int:
    todo = pending()
    if "--list" not in args:
        for tag, directory, meta in todo:
            pack.pack(directory)
            (pack.DIST / f"{tag}.md").write_text(notes(meta), "utf-8")
            (pack.DIST / f"{tag}.title").write_text(f"{meta['name']} v{meta['version']}", "utf-8")
    tags = [tag for tag, _, _ in todo]
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as file:
            file.write(f"tags={' '.join(tags)}\n")
    print("\n".join(tags) if tags else "没有要发的版本")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
