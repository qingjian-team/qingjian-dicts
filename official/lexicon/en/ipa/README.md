# 青简英文音标表

英文候选旁显示的音标（General American，如 `cargo /ˈkɑrɡoʊ/`），随输入法安装；设置里打开「显示英文音标」后显示。

| 文件 | 内容 | 打包 |
| --- | --- | --- |
| `english-ipa.tsv` | `词\t/音标/`，只收纯小写字母的词，多音词取第一个读音 | 是 |
| `LICENSE-cmudict.txt` | CMU Pronouncing Dictionary 的许可原文（BSD-2-Clause） | 否 |

来源是 [CMU Pronouncing Dictionary](https://github.com/cmusphinx/cmudict) 的 `cmudict.dict`。ARPAbet 转 IPA 的规则（重音标在音节首、按最大起首音划音节、
无重音的 `AH` 记 `ə`）在输入法仓库 `tools/dict-convert/src/ipa.rs`。在输入法仓库（`ime/`，与本仓库并排放）里重新生成：

```bash
cargo run --release -p qingjian-dict-convert -- --out-dir ../qingjian-dicts/official/lexicon/en/ipa ipa <下载的 cmudict.dict>
```

CMUdict 不收规则派生的复数、过去式、进行式（`abacuses`、`abstracting`），产品英文词表里约 57% 的词有音标，查不到的就不显示。
