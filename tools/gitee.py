#!/usr/bin/env python3
"""把 GitHub 上的 Release 同步到 Gitee 镜像：同名发行版、同样的标题与说明、同样的附件。

    GITEE_TOKEN=… python3 tools/gitee.py            # 补齐全部
    GITEE_TOKEN=… python3 tools/gitee.py base-v1.0.0 …

设置页先从 Gitee 下，所以两边附件必须一模一样：Gitee 上缺的附件从 GitHub 下载后原样上传，传完从 Gitee 匿名下回来按 manifest.json 核对 SHA-256。
已有的发行版与附件不动，重复跑没有副作用。仓库内容（提交、标签）只推 GitHub，再在 Gitee 仓库页点同步过去；
这里只建发行版、传附件，用的都是同步过去的标签，不往 Gitee 推任何提交，免得两边分叉以后同步不了。标签还没到就先去 Gitee 点同步。
Gitee 一个仓库的附件总共不能超过 1GB，旧版本没人用了要删。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB = "qingjian-team/qingjian-dicts"
GITEE = "qingjian-team/qingjian-dicts"
API = f"https://gitee.com/api/v5/repos/{GITEE}"


def gitee(method: str, path: str, *form: str) -> object:
    """Gitee 接口出错时也可能回 200 加 {"message": …}，按有没有 message 判断；字段一律 --form-string，免得 @ 开头被当成文件。"""
    token = os.environ["GITEE_TOKEN"]
    if method == "GET":
        url = f"{API}{path}{'&' if '?' in path else '?'}access_token={token}"
        args = ["curl", "-sS", url]
    else:
        args = ["curl", "-sS", "-X", method, f"{API}{path}", "--form-string", f"access_token={token}", *form]
    out = json.loads(subprocess.run(args, check=True, capture_output=True, text=True).stdout or "null")
    if isinstance(out, dict) and "message" in out:
        sys.exit(f"Gitee {method} {path}：{out['message']}")
    return out


def github_releases(tags: list[str]) -> list[dict]:
    out = subprocess.run(
        ["gh", "release", "list", "-R", GITHUB, "--limit", "1000", "--exclude-drafts", "--json", "tagName,publishedAt"],
        check=True, capture_output=True, text=True,
    ).stdout
    found = sorted(json.loads(out), key=lambda release: release["publishedAt"])
    names = [release["tagName"] for release in found]
    missing = set(tags) - set(names)
    if missing:
        sys.exit(f"GitHub 上没有：{'、'.join(sorted(missing))}")
    releases = []
    for tag in (tags or names):
        view = subprocess.run(
            ["gh", "release", "view", tag, "-R", GITHUB, "--json", "name,body,assets"],
            check=True, capture_output=True, text=True,
        ).stdout
        releases.append({"tag": tag, **json.loads(view)})
    return releases


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(tag: str, stage: Path) -> None:
    """从 Gitee 匿名下回全部附件，按 manifest.json 核对。"""
    def fetch(name: str) -> Path:
        target = stage / f"gitee-{name}"
        url = f"https://gitee.com/{GITEE}/releases/download/{urllib.parse.quote(tag)}/{urllib.parse.quote(name)}"
        with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as file:
            while block := response.read(1 << 20):
                file.write(block)
        return target

    manifest = json.loads(fetch("manifest.json").read_text("utf-8"))
    for part in manifest["parts"]:
        path = fetch(part["name"])
        if path.stat().st_size != part["bytes"] or sha256(path) != part["sha256"]:
            sys.exit(f"{tag}：Gitee 上的 {part['name']} 和 manifest.json 对不上")


def sync(release: dict) -> None:
    tag = release["tag"]
    existing = gitee("GET", f"/releases/tags/{urllib.parse.quote(tag)}")
    if isinstance(existing, dict) and existing.get("id"):
        gitee_id, action = existing["id"], "已有"
    else:
        commit = subprocess.run(
            ["gh", "api", f"repos/{GITHUB}/commits/{tag}", "--jq", ".sha"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        created = gitee(
            "POST", "/releases",
            "--form-string", f"tag_name={tag}",
            "--form-string", f"name={release['name']}",
            "--form-string", f"body={release['body']}",
            "--form-string", "prerelease=false",
            "--form-string", f"target_commitish={commit}",
        )
        gitee_id, action = created["id"], "已创建"
    attached = {asset["name"] for asset in gitee("GET", f"/releases/{gitee_id}/attach_files?per_page=100")}
    with tempfile.TemporaryDirectory() as stage_name:
        stage = Path(stage_name)
        uploaded = []
        for asset in release["assets"]:
            if asset["name"] in attached:
                continue
            subprocess.run(
                ["gh", "release", "download", tag, "-R", GITHUB, "-p", asset["name"], "-D", str(stage)],
                check=True,
            )
            path = stage / asset["name"]
            gitee("POST", f"/releases/{gitee_id}/attach_files", "-F", f"file=@{path}")
            uploaded.append(asset["name"])
        verify(tag, stage)
    print(f"{tag}：发行版{action}，上传 {len(uploaded)} 个附件，核对通过")


def main(args: list[str]) -> int:
    if "GITEE_TOKEN" not in os.environ:
        sys.exit("要设 GITEE_TOKEN（对 Gitee 仓库有推送权限的私人令牌）")
    for release in github_releases(args):
        sync(release)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
