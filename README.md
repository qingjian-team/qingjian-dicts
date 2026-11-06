# 青简词库

[青简输入法](https://github.com/qingjian-team/qingjian)的词库仓库：青简自己维护的词库与释义表，以及社区收录的第三方词库。
词库和输入法分开放，是为了每本词库单独写清来源、作者与许可，互不牵连。

镜像：[GitHub](https://github.com/qingjian-team/qingjian-dicts) · [Gitee](https://gitee.com/qingjian-team/qingjian-dicts)

## 目录

| 目录 | 内容 |
| --- | --- |
| `official/base` | 基础词库，随输入法安装 |
| `official/english` | 英文词表，随输入法安装 |
| `official/domains/<领域>` | 11 本领域词库（医学、法律、地名……），在设置页「词库」里按需下载 |
| `official/glossary/<语言>` | 候选词右侧的释义表；英语随输入法安装，其余按需下载 |
| `official/upstream` | 上面几本的上游原始数据与许可原文 |
| `community/<id>` | 第三方词库，每本一个目录，带自己的许可与说明 |
| `tools/check.py` | 检查 `dict.toml` 与数据格式，CI 与提交钩子都跑它 |

每本词库目录里有一份 `dict.toml`：名字、类别、版本、作者、许可、哪部分是机器生成的，字段说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 怎么装

- **在输入法里下载**：设置页「词库」→「下载词库」，列表从本仓库实时取，Gitee 与 GitHub 哪边快用哪边。
- **手动导入**：到 Releases 下载 `.qjz`，在设置页「词库」→「导入」选它。

每本词库单独发 Release，标签是 `<id>-v主.次.修订`（如 `domain-medicine-v1.0.0`），附件是 `<id>.qjz` 与 `manifest.json`。
`.qjz` 是压缩过的 `.qj`，导入时输入法会解开并核对校验值。另有包含全部官方词库的完整包，给离线安装与发行版打包用。

## 许可

本仓库**没有统一的许可**，以每本词库 `dict.toml` 里的 `license` 为准，详见 [LICENSE.md](LICENSE.md)。
