# 青简英文词表

中英混输与英文模式用的英文词表，随输入法安装。

| 文件 | 内容 | 打包 |
| --- | --- | --- |
| `english.tsv` | 成品：`词\t编码\t词频`，词频是 wordfreq 的 Zipf 频率 × 1000 | 是 |
| `inputs/frequency.tsv` | 生成成品时并进去的词频（`编码\t词频`） | 否，已在成品里 |

词表来源在 [`../upstream/05_english/`](../upstream/05_english/)。生成在输入法仓库（`ime/`，与本仓库并排放）里跑，步骤见
[`../base/BUILD.md`](../base/BUILD.md) 的第 5 步：`dict-convert english` 出不带词频的一版，`tools/corpus/english_frequency.py`
按 wordfreq 算出 `inputs/frequency.tsv`，再带 `--frequency` 跑一次 `english` 得到 `english.tsv`。
