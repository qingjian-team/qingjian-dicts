# 贡献

改官方词库（补词、改读音、调词频）直接提 PR 改 `official/` 下对应的文件；收录第三方词库按下面「第三方词库」放进 `community/`。
提交前启用钩子：`git config core.hooksPath .githooks`，它会拦构建产物、跑 `tools/check.py`。

## dict.toml

每本词库目录一份：

```toml
id = "domain-medicine"        # 小写字母、数字、-；全仓库唯一，也是 Release 标签的前缀
name = "医学词库"
kind = "extra"                # base：可以替换基础词库的完整词库；extra：附加词库；glossary：释义表；wordlist：拼音以外的输入语言用的词表（英文、越南语）
language = "zh"               # ISO 639 代码：词库写输入语言，释义表写释义的语言（只给某种输入语言用的对照表写那种输入语言）；official/ 下要和所在的语言目录一致
version = "1.0.0"             # 主.次.修订；数据文件或 dict.toml 改了就升（PR 的检查会拦），合进 main 后自动发这个版本
description = "疾病、症状、药物与检查名称，约 1.6 万条。"  # 一句话说清收了什么、适合谁
author = { name = "青简", url = "https://qingjian.app" }  # 做这本词库的人或团队，只写一个；设置页显示它，点名字打开 url（可省，只收 https 域名）
credits = ["清华大学自然语言处理实验室（THUOCL）"]  # 许可要求署名的上游与贡献者，写进 .qj 元数据，设置页不列；没有可省
homepage = "https://github.com/qingjian-team/qingjian-dicts"
license = "MIT AND CC-BY-SA-4.0"  # SPDX 表达式，几份来源用 AND 连起来
machine_generated = "部分：多音字词读音由 LLM 标注"  # 或 false
format = "tsv"                # tsv（缺省）/ rime（.dict.yaml）/ words（一行一个词）
bundled = false               # 随输入法安装的写 true（只有官方的基础词库、英文词表、越南语词表与越南语→中文对照、英语释义表）；第三方不能随包

# 数据放在本目录，或者用下面的 [upstream]，二选一
files = ["words.tsv"]

# 第三方词库另外要写：
# maintainers = ["github-login"]   # 负责跟进上游更新的人
# [upstream]                       # 指向上游仓库的固定提交，发版时现取现转（这时不写 files）
# url = "https://github.com/…"
# commit = "<40 位提交号>"
# files = ["cn_dicts/base.dict.yaml"]
# sha256 = { "cn_dicts/base.dict.yaml" = "<64 位>" }
```

格式：

- `tsv`：词库是 `词\t拼音\t词频` 或 `词\t词频`（拼音音节用空格隔开，没有拼音可留空，输入法会补；词频是整数），
  释义表是 `词\t[词性. ]释义[|读音]\t…`。`#` 开头的行是注释。
- 一律 UTF-8 无 BOM、LF 换行。

## 第三方词库

放在 `community/<id>/`，目录里要有：

- `dict.toml`
- `LICENSE`：上游许可原文
- `README.md`：来源、怎么生成的、和上游有什么不同、已知问题

数据小、或上游已经不维护的，直接放进目录（`files`）；数据大、上游还在更新的，用 `[upstream]` 指向固定提交，不在本仓库存一份。
单个文件不能超过 50MB：大的按拼音首字母之类的规则拆成几个文件，列在 `files` 里（见 `official/lexicon/zh/general`），或者用 `[upstream]`。

`kind = "base"` 的完整词库，用户可以在输入法里拿它替换青简基础词库；输入法的排序是按青简自己的语料调的，换了词库排序效果由词库自己负责。

## 许可

只收能随开源输入法再分发、允许商用与修改的许可，白名单在 `tools/check.py` 的 `LICENSES`（CC0、CC BY、CC BY-SA、MIT、BSD、Apache-2.0、Unicode、ODbL、LGPL、GPL）。
禁止商用（NC）、禁止演绎（ND）、没写许可的一律不收。从别的输入法词表拷来的，许可跟着上游走，写进 `license` 并附原文。

## 提交信息

Conventional Commits：`<类型>(<范围>): <说明>`，范围写词库 id，例如 `fix(base): 朝阳市改读 chao yang`、`feat(domain-medicine): 补常见药名`。
