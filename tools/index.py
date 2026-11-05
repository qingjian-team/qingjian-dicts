#!/usr/bin/env python3
"""更新 index.json：输入法设置页「词库」→「获取列表」读的清单。

    python3 tools/index.py          # pack.py 打完会自己调

按 dist/*/manifest.json 更新或加上对应的词库（大小、格式版本），其余字段取各本 dict.toml；
dict.toml 已经删掉的从清单里去掉，dist 里没有的保留上次的记录（没重打的词库不用每次都打）。
随包的（bundled = true）不列：它们跟着输入法装。官方的排在第三方前面。
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.json"
SECTIONS = ("official", "community")

# 清单格式；改了字段的写法就加一，输入法的 dict_index 同时改
FORMAT = 1


def dict_tomls() -> dict[str, tuple[str, dict]]:
    found = {}
    for section in SECTIONS:
        for path in sorted((ROOT / section).rglob("dict.toml")):
            meta = tomllib.loads(path.read_text("utf-8"))
            found[meta["id"]] = (section, meta)
    return found


def main(args: list[str]) -> int:
    old = {}
    if INDEX.is_file():
        old = {entry["id"]: entry for entry in json.loads(INDEX.read_text("utf-8"))["dicts"]}
    manifests = {}
    for path in sorted((ROOT / "dist").glob("*/manifest.json")):
        manifest = json.loads(path.read_text("utf-8"))
        manifests[manifest["dict"]] = manifest

    entries = []
    for dict_id, (section, meta) in dict_tomls().items():
        if meta.get("bundled"):
            continue
        manifest = manifests.get(dict_id)
        previous = old.get(dict_id)
        if manifest is None and previous is None:
            continue
        if manifest is not None and manifest["version"] != meta["version"]:
            print(f"{dict_id}: dist 里是 {manifest['version']}，dict.toml 是 {meta['version']}，先重新打包", file=sys.stderr)
            return 1
        released = manifest or previous
        entries.append({
            "id": dict_id,
            "name": meta["name"],
            "kind": meta["kind"],
            **({"language": meta["language"]} if meta.get("language") else {}),
            "version": released["version"],
            "tag": released["tag"],
            "bytes": manifest["archive"]["bytes"] if manifest else previous["bytes"],
            "qj_format": released["qj_format"],
            "license": meta["license"],
            "description": meta["description"],
            "authors": meta["authors"],
            "machine_generated": meta["machine_generated"] or None,
            "official": section == "official",
        })
    entries.sort(key=lambda entry: (not entry["official"], entry["kind"] != "extra", entry["id"]))
    INDEX.write_text(json.dumps({"format": FORMAT, "dicts": entries}, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"index.json：{len(entries)} 本")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
