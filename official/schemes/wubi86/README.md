# 五笔（86）

随输入法安装的形码方案。`table.tsv` 是码表（`词\t编码\t词频`），打包成 `wubi86.qj`，输入法按编码前缀查。
方案的名字、作者、许可、版本与简介取 `dict.toml`，写进 `.qj` 的文件头；按键规则（自动上屏、顶字）用输入法的缺省，用户可在设置里改。

| 文件 | 来源 | 许可 |
| --- | --- | --- |
| `wubi86_jidian.dict.yaml`（上游源文件，8.9 万条，不进仓库） | 86 五笔极点码表，<https://github.com/sxjudya/rime-wubi86-jidian>（`version: "4.3"`） | Apache-2.0，原文见同目录 `LICENSE` |
| `table.tsv` | 由上面那份转换而来 | 编码来自上游（Apache-2.0）；词频是青简自己统计的 |

上游还有 `wubi86_jidian_extra.dict.yaml`（扩展词）与 `wubi86_jidian_extra_district.dict.yaml`（行政区域），**暂未并入**：
极点方案的 `import_tables` 收了前者，以后按需要再加。

同一单字母编码的词按上游码表顺序保留，保证一级简码排在其他同码单字之前；其余编码按青简词频排序。

## 词频不是码表自带的权重

码表第二列（Rime 的 `weight`）是码表顺序，不是语料词频。直接拿来排序，同一个词在五笔下和在拼音下会排得不一样，
释义兜底与生词识别也对不上。所以转换时**按词面**从青简词库回填词频：词库里有的用语料词频（与拼音方案同一把尺子），
没有的给 `UNKNOWN_FREQUENCY = 1`。

## 重新生成

先从上游仓库下载 `wubi86_jidian.dict.yaml`，在输入法仓库（`ime/`，与本仓库并排放）里跑（`--frequency` 建议给基础词库 + 全部领域词库，覆盖率更高）：

```bash
cargo run --release -p qingjian-dict-convert -- --out-dir ../qingjian-dicts/official/schemes/wubi86 wubi \
    <下载的 wubi86_jidian.dict.yaml> \
    --frequency ../qingjian-dicts/official/lexicon/zh/base/words.tsv ../qingjian-dicts/official/lexicon/zh/domains/*/words.tsv
```

命中率（2026-09-16，基础词库 + 领域词库）：8.9 万条里 5.67 万条拿到语料词频，3.25 万条是兜底。
兜底的那部分主要是《通用规范汉字表》之外的罕见字（菚 / 匞 / 葚 这类）与青简词库没收的成语、词组；
它们在候选里排在已知词后面，只有在同编码没有别的选择时才出现。
