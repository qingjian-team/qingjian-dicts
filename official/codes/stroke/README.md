# 笔画

随输入法安装的辅码码表：输入法里辅码选「笔画」时用它，按笔画筛候选。

`stroke.tsv` 是笔画表（`字\t笔顺`，1 横 / 2 竖 / 3 撇 / 5 折 / n 点与捺，按大陆笔顺），7,991 字。
打包时按取码规则算成码表 `stroke.qj`：单字取前 4 笔加末笔，词取每个字的首笔，词表用基础词库的 `words.tsv`（`dict.toml` 的 `dictionary`），有字不在笔画表里的词跳过。

| 文件 | 来源 | 许可 |
| --- | --- | --- |
| `stroke.tsv` | 「CNS11643 中文標準交換碼全字庫」筆順資料（數位發展部，<https://data.gov.tw/dataset/5961>），台湾笔顺按 [`official/upstream/stroke`](../../upstream/stroke/README.md) 的大陆序覆盖规则改写 | 政府資料開放授權條款第 1 版或 OFL-1.1，二选一，取 OFL-1.1，原文见同目录 `LICENSE` |

本表是派生数据（筆順資料 → 笔画码表），修改内容是大陆序覆盖规则。随包时数据目录要带 `LICENSE`，并在「关于」页署名資料來源。

## 重新生成

笔画表由输入法仓库的 dict-convert 生成，命令、验收与许可合规见 [`official/upstream/stroke/README.md`](../../upstream/stroke/README.md)，生成后拷到这里。基础词库加了词时笔画表不用重生成，但这本要升版本重新发版，词的编码才跟上。
