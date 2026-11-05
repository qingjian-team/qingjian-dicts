#!/usr/bin/env python3
"""把一本或几本词库打成 Release 附件：`dist/<id>-v<版本>/<id>.qjz` 与 `manifest.json`，再更新 index.json。

    python3 tools/pack.py official/domains/medicine official/general
    QINGJIAN_DICT_CONVERT=/path/to/qingjian-dict-convert python3 tools/pack.py …

`.qj` 由输入法仓库的 dict-convert 生成（缺省 ../ime/target/release/qingjian-dict-convert，
先在 ime 里 `cargo build --release -p qingjian-dict-convert`），元数据取 dict.toml：名字、许可、作者、主页、版本。
manifest.json 与模型仓库的同一个格式（archive + parts），输入法的下载代码两边共用；词库压完都不到 95MB，只有一块。
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CONVERT = Path(os.environ.get("QINGJIAN_DICT_CONVERT", ROOT.parent / "ime/target/release/qingjian-dict-convert"))

# Gitee 单个附件的上限留出余量；超了要像模型仓库那样切块
PART_LIMIT = 95 * 1000 * 1000

sys.path.insert(0, str(ROOT / "tools"))
import index  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def build_qj(directory: Path, meta: dict, stage: Path) -> Path:
    if meta.get("format", "tsv") != "tsv" or not meta.get("files"):
        sys.exit(f"{directory}: 只能打 format = \"tsv\"、数据放在本目录（files）的词库")
    inputs = [str(directory / name) for name in meta["files"]]
    common = [
        "--name", meta["name"],
        "--license", meta["license"],
        "--attribution", "、".join(meta["authors"]),
        "--source", meta.get("homepage", ""),
        "--data-version", meta["version"],
    ]
    kind = meta["kind"]
    if kind in ("base", "extra"):
        args, out = ["pack", "dict", "--input", *inputs], stage / "dict.qj"
    elif kind == "glossary":
        language = meta["language"]
        args, out = ["pack", "glossary", "--language", language, "--input", inputs[0]], stage / f"glossary-{language}.qj"
    else:
        sys.exit(f"{directory}: kind = {kind} 不发 Release")
    subprocess.run([str(CONVERT), "--out-dir", str(stage), *args, *common], check=True)
    return out


def pack(directory: Path) -> Path:
    meta = tomllib.loads((directory / "dict.toml").read_text("utf-8"))
    tag = f"{meta['id']}-v{meta['version']}"
    out = DIST / tag
    with tempfile.TemporaryDirectory() as stage_name:
        stage = Path(stage_name)
        qj = build_qj(directory, meta, stage)
        subprocess.run([str(CONVERT), "--out-dir", str(stage), "qjz", str(qj)], check=True)
        packed = qj.with_suffix(".qjz")
        if packed.stat().st_size > PART_LIMIT:
            sys.exit(f"{directory}: 压完 {packed.stat().st_size} 字节，超过一块的上限，要先补上切块")
        out.mkdir(parents=True, exist_ok=True)
        target = out / f"{meta['id']}.qjz"
        packed.replace(target)
    with gzip.open(target, "rb") as file:
        header = file.read(12)
    qj_format = int.from_bytes(header[8:10], "little")
    piece = {"bytes": target.stat().st_size, "sha256": sha256(target)}
    manifest = {
        "dict": meta["id"],
        "version": meta["version"],
        "tag": tag,
        "qj_format": qj_format,
        "archive": piece,
        "parts": [{"name": target.name, **piece}],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"{tag}: {piece['bytes']} 字节")
    return out


def main(args: list[str]) -> int:
    if not args:
        sys.exit(__doc__)
    if not CONVERT.is_file():
        sys.exit(f"找不到 dict-convert：{CONVERT}")
    for name in args:
        pack((ROOT / name).resolve())
    return index.main([])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
