#!/usr/bin/env python3
"""检查每本词库的 dict.toml 与数据文件：字段齐全、id 不重复、许可在白名单里、文本格式对。

    python3 tools/check.py            # 全部
    python3 tools/check.py official/lexicon/zh/domains/medicine
    python3 tools/check.py --since origin/main   # 另查：数据或 dict.toml 改了的词库 version 有没有升（PR 的 CI 这样跑）

字段含义见 CONTRIBUTING.md「dict.toml」。CI 与 pre-commit 都跑它，有一条不过就非零退出。
"""

from __future__ import annotations

import ipaddress
import re
import subprocess
import sys
import tomllib
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ("official", "community")

KINDS = {"base", "extra", "glossary", "wordlist", "pronunciation", "scheme", "codes"}
FORMATS = {"tsv", "rime", "words"}

# 允许的 SPDX 许可：能随开源输入法再分发、允许商用与修改。NC / ND 一类不收，见 CONTRIBUTING.md「许可」。
LICENSES = {
    "CC0-1.0",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "OFL-1.1",
    "Unicode-3.0",
    "ODbL-1.0",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
}

LANGUAGE = re.compile(r"^[a-z]{2,3}$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def license_ids(expression: str) -> list[str]:
    """把 `MIT AND (CC-BY-SA-4.0 OR GPL-3.0-or-later)` 拆成各个许可 id。"""
    tokens = re.split(r"[\s()]+", expression)
    return [t for t in tokens if t and t not in {"AND", "OR", "WITH"}]


def check_author(author) -> list[str]:
    """author 写 { name = "…", url = "https://…" }，url 可省；地址会在设置页里点开，所以收紧。"""
    if not isinstance(author, dict) or not str(author.get("name", "")).strip():
        return ['author 写成 { name = "名字", url = "https://主页" }，url 可省']
    extra = set(author) - {"name", "url"}
    if extra:
        return [f"author 只认 name 与 url，多了 {sorted(extra)}"]
    url = author.get("url")
    if url is None:
        return []
    parts = urllib.parse.urlsplit(str(url))
    host = parts.hostname or ""
    if parts.scheme != "https" or not host:
        return [f"author.url {url!r} 要写 https 地址"]
    if "@" in parts.netloc:
        return [f"author.url {url!r} 不能带用户名（@）"]
    try:
        ipaddress.ip_address(host)
        return [f"author.url {url!r} 要写域名，不写 IP"]
    except ValueError:
        pass
    if "." not in host or any(label.startswith("xn--") for label in host.split(".")):
        return [f"author.url {url!r} 的域名要是普通的 ASCII 域名（不收 xn-- 开头的国际化域名，防仿冒）"]
    return []


def check_meta(path: Path, meta: dict, section: str) -> list[str]:
    errors = []
    need = ["id", "name", "kind", "language", "version", "description", "author", "license", "machine_generated"]
    for key in need:
        if key not in meta:
            errors.append(f"缺 {key}")
    if errors:
        return errors

    if not ID.match(meta["id"]):
        errors.append(f"id {meta['id']!r} 只能用小写字母、数字和 -，2～41 个字符")
    if meta["kind"] not in KINDS:
        errors.append(f"kind {meta['kind']!r} 不认识，可选 {sorted(KINDS)}")
    if not LANGUAGE.match(str(meta["language"])):
        errors.append(f"language {meta['language']!r} 要写 ISO 639 代码（zh、en、ja……）")
    rel = path.parent.relative_to(ROOT).parts
    if rel[:2] in (("official", "lexicon"), ("official", "glossary")) and len(rel) > 2 and rel[2] != meta["language"]:
        errors.append(f"放在 {'/'.join(rel[:3])} 下，language 却是 {meta['language']!r}")
    if meta["kind"] in ("pronunciation", "scheme", "codes") and not meta.get("bundled"):
        errors.append("音标表、形码方案与辅码码表现在只随包（bundled = true），设置页的下载列表不列它们")
    if meta["kind"] == "codes" and not (path.parent / str(meta.get("dictionary", ""))).is_file():
        errors.append("辅码码表要写 dictionary：算词的编码用的词库（相对本目录的路径）")
    if "glossary" in meta:
        errors.append("glossary 字段已去掉：附带的对照表单独做一本 kind = \"glossary\" 的词库")
    if not VERSION.match(str(meta["version"])):
        errors.append(f"version {meta['version']!r} 要写成 主.次.修订")
    if "authors" in meta:
        errors.append("authors 已改成 author（做这本的人或团队，一个）加 credits（上游与外部贡献的署名）")
    errors.extend(check_author(meta["author"]))
    credits = meta.get("credits", [])
    if not isinstance(credits, list) or not all(isinstance(c, str) and c.strip() for c in credits):
        errors.append("credits 写名字的列表")
    generated = meta["machine_generated"]
    if not (generated is False or (isinstance(generated, str) and generated.strip())):
        errors.append("machine_generated 写 false，或用一句话说明哪部分是机器生成的")
    for lic in license_ids(meta["license"]):
        if lic not in LICENSES:
            errors.append(f"许可 {lic} 不在白名单里（CONTRIBUTING.md「许可」）")
    if meta.get("format", "tsv") not in FORMATS:
        errors.append(f"format {meta['format']!r} 不认识，可选 {sorted(FORMATS)}")

    if section == "community":
        if meta.get("bundled"):
            errors.append("第三方词库不能随包（bundled）")
        if not any(path.parent.glob("LICENSE*")):
            errors.append("第三方词库目录里要放上游的许可原文 LICENSE")
        if not (path.parent / "README.md").is_file():
            errors.append("第三方词库目录里要有 README.md（来源、怎么生成、和上游的差别）")

    files, upstream = meta.get("files"), meta.get("upstream")
    if bool(files) == bool(upstream):
        errors.append("files（数据放在本目录）和 [upstream]（指向上游固定提交）二选一")
    if upstream:
        if not str(upstream.get("url", "")).startswith("https://"):
            errors.append("upstream.url 要写 https 地址")
        if not COMMIT.match(str(upstream.get("commit", ""))):
            errors.append("upstream.commit 要写完整的 40 位提交号，不写分支名")
        if not upstream.get("files"):
            errors.append("upstream.files 要列出上游仓库里用到的文件")
        for digest in (upstream.get("sha256") or {}).values():
            if not SHA256.match(str(digest)):
                errors.append(f"upstream.sha256 {digest!r} 不是 64 位十六进制")
    return errors


def check_text(file: Path, kind: str, fmt: str) -> list[str]:
    data = file.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return [f"{file.name} 带 BOM"]
    if b"\r" in data:
        return [f"{file.name} 要用 LF 换行"]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        return [f"{file.name} 不是 UTF-8：{error}"]

    lines = text.split("\n")
    if fmt == "rime":
        if "\n...\n" not in text:
            return [f"{file.name} 找不到 Rime 词库头的结束行 ..."]
        lines = text.split("\n...\n", 1)[1].split("\n")

    errors = []
    for number, line in enumerate(lines, 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if not fields[0].strip():
            errors.append(f"{file.name}:{number} 第一列是空的")
        elif fmt == "words" and len(fields) != 1:
            errors.append(f"{file.name}:{number} 只有词的表一行一个词，不带 Tab")
        elif fmt == "tsv" and kind == "glossary" and (len(fields) < 2 or not fields[1].strip()):
            errors.append(f"{file.name}:{number} 释义表要有「词\\t释义」")
        elif fmt == "tsv" and kind == "scheme":
            if len(fields) not in (2, 3) or not fields[1].isascii() or not fields[1].isalpha() or (len(fields) == 3 and not fields[2].isdigit()):
                errors.append(f"{file.name}:{number} 码表要写成「词\\t编码\\t词频」，编码只用字母")
        elif fmt == "tsv" and kind == "codes":
            if len(fields) != 2 or len(fields[0]) != 1 or not fields[1] or set(fields[1]) - set("1235n"):
                errors.append(f"{file.name}:{number} 笔画表要写成「字\\t笔顺」，笔顺只用 1 2 3 5 n")
        elif fmt == "tsv" and kind == "pronunciation":
            if len(fields) != 2 or not (fields[1].startswith("/") and fields[1].endswith("/") and len(fields[1]) > 2):
                errors.append(f"{file.name}:{number} 音标表要写成「词\\t/音标/」")
        elif fmt == "tsv" and kind != "glossary":
            if len(fields) not in (2, 3) or not fields[-1].isdigit():
                errors.append(f"{file.name}:{number} 要写成「词\\t拼音\\t词频」或「词\\t词频」，词频是整数")
        if len(errors) >= 5:
            errors.append(f"{file.name} 后面的行不再列出")
            break
    return errors


# 基础词库 inputs/ 里重新生成 words.tsv 时要 --extra-words 并入的五份（BUILD.md 第 4 步）；general-subset.tsv 另有挑选规则，不在其列
BASE = ROOT / "official/lexicon/zh/base"
EXTRA_WORDS = ("mined.tsv", "phrases.tsv", "brands.tsv", "manual.tsv", "mixed.tsv")


def first_column(file: Path, need_count: bool = False) -> set[str]:
    words = set()
    for line in file.read_text("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if need_count and (len(fields) < 3 or not fields[2].strip().isdigit()):
            continue
        words.add(fields[0].strip())
    return words


def check_base_inputs() -> list[str]:
    """重新生成基础词库时少给一份 --extra-words，那批词会悄悄没了：inputs/ 的每个词都要在基础词库或领域词库里。"""
    generated = first_column(BASE / "words.tsv") | first_column(BASE / "supplement.tsv")
    for words in sorted((ROOT / "official/lexicon/zh/domains").glob("*/words.tsv")):
        generated |= first_column(words)
    errors = []
    for name in EXTRA_WORDS:
        missing = sorted(first_column(BASE / "inputs" / name, need_count=True) - generated)
        if missing:
            errors.append(f"inputs/{name} 里 {len(missing)} 个词不在 words.tsv 与领域词库里（重新生成时漏了 --extra-words？）：{missing[:10]}")
    return errors


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def check_versions(since: str) -> int:
    """数据文件或 dict.toml 改了，version 就要和 since 那边不同：输入法按版本号判断有没有更新，CI 按版本号发版。"""
    old = {}
    for name in git("ls-tree", "-r", "--name-only", since).splitlines():
        if name.endswith("/dict.toml") and name.split("/", 1)[0] in SECTIONS:
            meta = tomllib.loads(git("show", f"{since}:{name}"))
            old[meta["id"]] = meta["version"]
    changed = set()
    for line in git("diff", "--name-status", "-M", f"{since}...HEAD").splitlines():
        status, *names = line.split("\t")
        if status != "R100":  # 只挪了位置、内容没变的不算改
            changed.add(names[-1])
    failed = 0
    for path in (p for s in SECTIONS for p in sorted((ROOT / s).rglob("dict.toml"))):
        meta = tomllib.loads(path.read_text("utf-8"))
        if meta["id"] not in old:
            continue
        directory = path.parent.relative_to(ROOT).as_posix()
        packed = ["dict.toml", *(meta.get("files") or [])]
        touched = [name for name in packed if f"{directory}/{name}" in changed]
        if touched and meta["version"] == old[meta["id"]]:
            print(f"{directory}: 改了 {'、'.join(touched)}，version 还是 {meta['version']}，要升一号")
            failed += 1
    return failed


def main(args: list[str]) -> int:
    since = None
    if args[:1] == ["--since"] and len(args) > 1:
        since, args = args[1], args[2:]
    if args:
        tomls = [ROOT / a / "dict.toml" for a in args]
    else:
        tomls = [p for s in SECTIONS for p in sorted((ROOT / s).rglob("dict.toml"))]  # official 在前，重复 id 记在第三方头上
    seen: dict[str, Path] = {}
    if args:  # 只查几本时也要和全部的 id 比重复
        for p in (p for s in SECTIONS for p in (ROOT / s).rglob("dict.toml")):
            try:
                seen.setdefault(tomllib.loads(p.read_text("utf-8"))["id"], p)
            except (tomllib.TOMLDecodeError, KeyError):
                pass
    failed = 0
    for path in tomls:
        rel = path.relative_to(ROOT)
        section = rel.parts[0]
        try:
            meta = tomllib.loads(path.read_text("utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            print(f"{rel}: 读不了：{error}")
            failed += 1
            continue
        errors = check_meta(path, meta, section)
        owner = seen.get(meta.get("id"))
        if owner and owner != path:
            errors.append(f"id {meta['id']} 与 {owner.relative_to(ROOT)} 重复")
        seen.setdefault(meta.get("id"), path)
        for name in meta.get("files") or []:
            file = path.parent / name
            if not file.is_file():
                errors.append(f"files 里的 {name} 不存在")
            else:
                errors += check_text(file, meta.get("kind", ""), meta.get("format", "tsv"))
        for error in errors:
            print(f"{rel.parent}: {error}")
        failed += bool(errors)
    if BASE / "dict.toml" in tomls:
        for error in check_base_inputs():
            print(f"{BASE.relative_to(ROOT)}: {error}")
            failed += 1
    print(f"查了 {len(tomls)} 本，{failed} 本有问题" if failed else f"查了 {len(tomls)} 本，都没问题")
    if since is not None and not failed:
        failed = check_versions(since)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
