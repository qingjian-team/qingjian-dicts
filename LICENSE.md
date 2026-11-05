# 许可

本仓库没有统一的许可：每本词库的许可写在它目录下 `dict.toml` 的 `license`（SPDX 表达式），以那里为准。

- **青简整理的部分**（`official/` 下由青简团队整理、标注、统计的内容）：[CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt)。
- **外部贡献者在本仓库拆出之前贡献的内容**：按当时输入法仓库的 [GPL-3.0-or-later](LICENSES/GPL-3.0-or-later.txt) 收入，继续按 GPL-3.0-or-later 提供。
  整本是外部贡献的（德语、西班牙语、越南语释义表）整本标 GPL；混在青简词库里的条目，`dict.toml` 的 `license` 里带上 GPL。
- **上游数据**：保留原许可，原文在 `official/sources/`（THUOCL 的 MIT、Unicode License、ESDB、CSpell、typos 等）。
- **第三方词库**（`community/`）：各自目录里的 `LICENSE` 与 `dict.toml`。

工具脚本（`tools/`、`.githooks/`、`pack.sh`）按 GPL-3.0-or-later 提供，与输入法一致。
