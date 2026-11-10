# 拆字表

问字模式按部件找字（`umumu` → 林、`uheszh` → 和）的源数据：一行一个字，Tab 分隔，
后面是一到六种拆法，拆法里的部件用空格分隔（`谢\t言 射\t讠 射`）。简体一份、繁体一份。

## 数据来源

| 文件 | 来源 | 许可 |
| --- | --- | --- |
| `chaizi-jt.txt` | [開放詞典網](http://kaifangcidian.com/) 的漢語拆字字典**簡體版**，[kfcd/chaizi](https://github.com/kfcd/chaizi) 提交 `e177ab54`（2017-08-31） | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/)，原文见 `LICENSE` |
| `chaizi-ft.txt` | 同一个仓库的**繁体版**（`chaizi-ft.txt`） | 同上 |
| `fanjian_suoyin.txt` | 同一个仓库的繁简索引（`繁体\t简体`，一行一对） | 同上 |

原样收录，未作改动。

## 繁体怎么进来

繁体表里「简体表没有的字」按 `fanjian_suoyin.txt` 落到简体主键（`謝` → `谢`），拆法并进同一个字——
于是打台北字形的拆法（`辶 言`，`uzouyan`）也能找到简体字，输出侧照旧由 Core 的 `Traditional` 在出口转。
索引里没有简体对应的字（繁简索引写成 `□` 占位的那种）保留原形，不丢。

`□` 这类方框符号是拆字字典里的占位部件，不是字：字列直接跳过，只作为部件留在拆法里。

部件别名表（俗名读音、CNS 没有的笔画符号）是青简手工维护、直接编进输入法的，不在本目录，在输入法仓库的 `crates/qingjian-core/data/parts.tsv`。

## 生成

生成工具在输入法仓库（[qingjian-team/qingjian](https://github.com/qingjian-team/qingjian)），下面的命令在输入法仓库根目录跑，本仓库与它放在同一级目录。

```bash
# 拆字表：简体 + 繁体 + 繁简索引 + 词库读音（../qingjian-dicts/official/lexicon/zh/base/words.tsv） → crates/qingjian-core/data/chaizi.tsv
cargo run -p qingjian-dict-convert -- --out-dir crates/qingjian-core/data chaizi

# 笔顺表（键位形式，给问字模式按笔画找字）：把部件别名表也当一张字表传进去，部件的笔顺才补得上
cargo run -p qingjian-dict-convert -- --out-dir crates/qingjian-core/data stroke \
  --cns-count data/cns/CNS_stroke.txt \
  --filter ../qingjian-dicts/official/upstream/01_characters/standard_8105.tsv,../qingjian-dicts/official/upstream/chaizi/chaizi-ft.txt,crates/qingjian-core/data/parts.tsv \
  --output crates/qingjian-core/data/stroke.tsv --keys
```

产物都是生成物，随包前由 `cargo run -p qingjian-dict-convert -- pack codes` 另算码表（辅码态用，与本目录无关）。
