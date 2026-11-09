# 青简基础词库：文件与构建

## 本目录的文件

| 文件 | 内容 | 打包 |
| --- | --- | --- |
| `words.tsv` | 主表：规范汉字、常用词、语料高频领域词，并好了 `inputs/` 的补充表，带语料词频。它也是训练语言模型时的分词词表 | 是 |
| `supplement.tsv` | 补充词：从通用扩展词库（V7）挑进来、主表没有的词与读音，词频已换算，与主表同一档。**不进分词词表**，所以和主表分开放：并进主表会改变语言模型 | 是 |
| `inputs/phrases.tsv` | 语料挖出的高频短语（下面 4c） | 否，已在主表里 |
| `inputs/mined.tsv` | 语料挖出、原词库没收的词（4b） | 否，已在主表里 |
| `inputs/manual.tsv` | 人工补充的词：输入日志里选过的、jieba 高频缺词、issue 点名的（4d） | 否，已在主表里 |
| `inputs/mixed.tsv` | 中英混杂词（4e） | 否，已在主表里 |
| `inputs/brands.tsv` | 品牌词 | 否，已在主表里 |
| `inputs/general-subset.tsv` | 通用扩展词库 V7 里机器初筛较好的 247,571 条原始子集（权重是原始的），`lexicon --cleaned` 由它生成 `supplement.tsv`（4f） | 否，用的是生成结果 |

上游原始数据在 [`../../../upstream/`](../../../upstream/)。

下面的命令都在输入法仓库（`ime/`，与本仓库并排放）里跑，工具是那边的 `qingjian-dict-convert` 与 `qingjian-gloss-gen`；
`lexicon` 生成的 `dict.tsv` 就是这里的 `words.tsv`，已清洗子集的生成结果 `dict-cleaned.tsv` 就是 `supplement.tsv`。
工具的缺省路径就指着本仓库（`../qingjian-dicts/official/...`），两个仓库并排放时不用另给路径参数。

## 上游数据的来历

这是青简自己的词库来源，从「输入法字词库_分类整理版」数据包拷入（2026-09-05），只去掉了与 TSV 内容相同的 TXT 副本；
目录与文件名改成了 ASCII（GitHub 链接、各平台 shell 都省事），对照：`00_说明与校验 → 00_meta`、`01_标准字库 → 01_characters`、
`02_通用词库 → 02_common`、`03_领域词库 → 03_domains`、`04_网络用语_待采集 → 04_internet_slang`、`05_英文词库 → 05_english`，
文件名同理（`现代汉语常用词 → modern_chinese_common_words`、领域按英文名）。`00_meta/SHA256SUMS.txt` 里记的是原始文件名与校验值。
这些都在 [`../../../upstream/`](../../../upstream/)：数据包自身的说明见 [README.md](../../../upstream/README.md)，英文部分见 [05_english/README.md](../../../upstream/05_english/README.md)，
各来源许可证原文在 `00_meta/` 与 `05_english/sources/`。

## 怎么变成输入法用的词库

```bash
# lexicon 的各项输入缺省都并入：LLM 读音 data/generated/pinyin-llm.jsonl、语料词频 data/generated/lm-unigram.tsv、
# inputs/ 的五份额外词（挖词 / 短语 / 品牌 / 人工补充 / 中英混杂，check.py 会查它们都并进了 words.tsv）、青简词库 data/lexicon/（仓库外的交付目录软链过来）。
# 缺文件就报错停下，不悄悄少并；从头重建时还没生成的用 --no-pinyin / --no-frequency / --no-extra-words / --no-general 排除。
# 1. 第一遍：写初版 dict.tsv，并列出要交给 LLM 定读音的词：没有拼音的领域词里含多音字的，以及常用词表里含多音字的
#    （常用词表自带的拼音对多音字有错，如 重庆 zhong4'qing4，所以也要标；标注与原表不同时标注为主读音，原表读音降权保留）
cargo run --release -p qingjian-dict-convert -- lexicon --no-pinyin --no-frequency --no-extra-words --no-general --emit-ambiguous data/generated/lexicon-ambiguous.txt
# 2. 多音字词交给 LLM 标读音（可中断续跑；结果 data/generated/pinyin-llm.jsonl，不进 git，发布时作为 Release 附件保存）
cargo run --release -p qingjian-gloss-gen -- pinyin
# 3. 用初版词库分词、统计语料词频（语料在 data/corpus/，见 docs/design/landscape.md）
cargo run --release -p qingjian-dict-convert -- bigram data/corpus/*.txt
# 4. 第二遍：带标注与词频写最终 dict.tsv；再统计一次语料让分词用上真实词频
#    领域词同时拆出：语料里 ≥ 50 次（--domain-keep-min）的留在 dict.tsv，其余按来源文件各写一本 dicts/<领域>.tsv + dicts/<领域>.qj（带 META）；
#    bigram / mine 分词时会自动把 dicts/*.tsv 一起当词表，所以拆分不影响语言模型
cargo run --release -p qingjian-dict-convert -- lexicon --no-extra-words --no-general
cargo run --release -p qingjian-dict-convert -- bigram data/corpus/*.txt
# 4b. 语料挖词库没收的高频词（分词落成连续单字的段），mine 自带虚词规则 + 相邻字对 PMI≥3 过滤（--min-pmi 调，
#     --candidates 可跳过扫语料只重过滤）：写 oov-candidates.tsv（原始）、oov-filtered.tsv（过滤后，拷成 ../qingjian-dicts/official/lexicon/zh/base/inputs/mined.tsv）、
#     oov-words.txt（交 gloss-gen pinyin 标音）；lexicon 用 --extra-words 只给它并入，然后重跑一次 bigram。
#     注意 PMI 用当前的一元表：并入挖出的词并重跑 bigram 之后单字次数会变，再挖一遍结果不同是正常的
cargo run --release -p qingjian-dict-convert -- mine data/corpus/*.txt
cp data/generated/oov-filtered.tsv ../qingjian-dicts/official/lexicon/zh/base/inputs/mined.tsv
cargo run --release -p qingjian-dict-convert -- lexicon --extra-words ../qingjian-dicts/official/lexicon/zh/base/inputs/mined.tsv --no-general
# 4c. 短语层：常用词表是词典词头，不收 我的 / 好的 / 不知道 / 有没有 这类人会整块打的组合。phrases 从 4 步统计出的 bigram 表取相邻两词、
#     扫语料取相邻三词（两遍），总次数与对话语料（--dialogue，缺省 lccc.txt）次数都 ≥ 2000（--min-count）、边界像话（不以 的了着 开头、不以 不没很也都 与数词结尾）、词库没有的写 phrases.tsv，
#     读音由成分词拼出不用再标；人工过一遍拷成 ../qingjian-dicts/official/lexicon/zh/base/inputs/phrases.tsv，与 mined_words.tsv、brand.tsv（品牌词 青简）等缺省的五份一起并入，再重跑 bigram。
#     词库已并入过短语时重跑要加 --refresh ../qingjian-dicts/official/lexicon/zh/base/inputs/phrases.tsv（先把上次的短语从分词词表摘掉，否则 我的 是一个词、挖不出 我 + 的）
cargo run --release -p qingjian-dict-convert -- phrases data/corpus/*.txt   # 重跑：--refresh ../qingjian-dicts/official/lexicon/zh/base/inputs/phrases.tsv
cp data/generated/phrases.tsv ../qingjian-dicts/official/lexicon/zh/base/inputs/phrases.tsv
cargo run --release -p qingjian-dict-convert -- lexicon --no-general
#     语言模型不把短语当 token 统计（那样 而 + 是 的二元证据没了，二十 会压过 而是）：--phrases 让分词跳过短语、统计完按成分合成它们的计数，
#     短语在整句与词级排序里的得分与原来走两个词的路径完全一样，只是多了个能整块选的词（见 tools/dict-convert/src/bigram.rs 模块注释）
cargo run --release -p qingjian-dict-convert -- bigram --phrases ../qingjian-dicts/official/lexicon/zh/base/inputs/phrases.tsv --phrases ../qingjian-dicts/official/lexicon/zh/base/inputs/manual.tsv --brand ../qingjian-dicts/official/lexicon/zh/base/inputs/brands.tsv --brand ../qingjian-dicts/official/lexicon/zh/base/inputs/mixed.tsv data/corpus/*.txt
# 4d. 领域词：输入日志里选过、词库与短语层都没有、但公开语料里出现过的词（对齐 / 后端 / 词库 / 候选框），人工挑进 ../qingjian-dicts/official/lexicon/zh/base/inputs/manual.tsv（词\t拼音\t次数，
#     次数用语料次数，不到 20 的按 20；只在日志里出现的不进基础词库，留在个人词库）。语言模型里它们**也走 --phrases 的合成路**：
#     语料里只有几十次的词当 token 统计会把成分词的二元证据吸走（词库 77 次，词 + 库 的路径没了，反被 词哭 压过），合成计数则整句得分与原路径一样，词级多一个能整块选的词。
#     见 docs/notes/domain-words.md
# 4e. 中英混杂词（C盘 / B站 / U盘 / T恤）：../qingjian-dicts/official/lexicon/zh/base/inputs/mixed.tsv（词\t拼音\t次数，字母音节 + 汉字拼音），
#     与 phrases / manual 一样是 lexicon 缺省并入的额外词；语言模型走 bigram --brand 直接写一元（--phrases 的合成要成分词在语料里，C 不是 token）。
#     次数对着同音竞争词定：C盘 8000 > 裁判 5416 可以抢首选；B站 要 40000：本站 7533 次里六成在句首（维基页脚），--brand 的句首二元按八分之一算，得盖过 4562；B股 / H股 / G盘 / F盘 / X光 压到几百，别压过 不顾 / 回顾 / 光盘 / 翻盘 / 星光。
# 4f. 青简词库：数字声调版全量（158 万条）与已清洗子集两个文件放在仓库外，交付目录软链成 data/lexicon（ln -s <交付目录> data/lexicon）后 lexicon 缺省就并入；
#     路径不同就用 --general / --cleaned 给（已清洗子集就是本仓库的 inputs/general-subset.tsv）。
#     基础词库已有的词补声调；没有的换算词频，已清洗的写 data/generated/dict-cleaned.tsv（pack dict 与 dict.tsv 合成 dict.qj，同一档），
#     其余写 dict-general.tsv 与 dicts/general.qj（随包，缺省开着、排序低一档）。都不进 bigram 分词，dict.tsv 除声调外不变，语言模型不用重跑
cargo run --release -p qingjian-dict-convert -- lexicon
# 5. 英文词表
cargo run --release -p qingjian-dict-convert -- english ../qingjian-dicts/official/upstream/05_english/00_all_words.tsv ../qingjian-dicts/official/upstream/05_english/07_display_forms.tsv
uv run tools/corpus/english_frequency.py data/generated/english.tsv -o data/generated/english-frequency.tsv
cargo run --release -p qingjian-dict-convert -- english ../qingjian-dicts/official/upstream/05_english/00_all_words.tsv ../qingjian-dicts/official/upstream/05_english/07_display_forms.tsv --frequency data/generated/english-frequency.tsv
# 6. 打包（bundle.sh 会自动做；领域词库的 .qj 第 4 步已经写好，bundle.sh 直接拷进 Resources/dicts/）
cargo run --release -p qingjian-dict-convert -- pack dict --name 青简基础词库 --license "MIT AND Unicode-3.0 AND GPL-3.0-or-later"
```

生僻字表 `../../../upstream/01_characters/rare_chars.tsv` 不在原数据包里，由 `tools/corpus/rare_chars.py` 从两张表合成（来源、读音出处与许可见脚本文件头）：
「规范字表外扩充汉字」（GB 18030-2022 原版范围的 Unicode 统一汉字减去 8105 字，读音取 Unihan 17）与台湾教育部罕用字 C 表（读音取 CNS 全字库），
按字去重、读音取并集，扩展 G 的 𰻝 𰻞 手工补。`lexicon` 每次都会读它，词库已有的字不动，其余按词频 0 收进 `dict.tsv`（不进语言模型与整句），
标了 `everyday` 的日常常用字（诶 囧）按规范字处理。

读音来自 Unihan（`data/unihan/Unihan_Readings.txt`，从 https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip 解出，Unicode License v3）；
多音字词的读音由 LLM 标注后逐字对照 Unihan 校验。最终的基础词库（`words.tsv` 与 `supplement.tsv`）放在本目录、拆出的领域词库在 `../domains/`，没有语料和 API 也能直接打包。
