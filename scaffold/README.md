# 脚手架 / Scaffold：应用型书籍 → 本体驱动系统

从 `cuisine_lab` 实战抽象出的**最小可复用骨架**，四阶段 + 四能力，纯标准库即可运行。

```bash
python3 scaffold/ontology_scaffold.py
```

## 它包含什么 / What it contains

| 阶段 | 函数 | 作用 | 本项目真实实现 |
|---|---|---|---|
| P1 结构抽取 | `structure(source)` | 按源标记确定性抽对象 | `pipeline/foodlab/epub_parse.py` |
| P2 语义归一 | `Vocabulary` + `normalize()` | 受控词表 + 别名/最长子串归一 | `taxonomy.py` + `llm_extract.py` + `translate.py` |
| P3 入库 | `store()` | 最小 schema（实体/部件/词表/关系/状态） | `pipeline/foodlab/db.py` |
| P4 应用 | `query/search/analysis/recommend` | 四能力 | `webapp.py` + `food_lexicon.py` |

## 五种可直接复用的模式 / Reusable patterns

1. **受控词表归一**：`Vocabulary.normalize()` —— 精确命中 → **最长子串**命中 → `None`（未命中保留，便于增量扩表）。
2. **双列联 schema**：`entities / parts / vocab / relations / status`（实体–部件–词表–关系–状态）。
3. **断点续跑**：`store()` 跳过 `status='ok'` 的实体；真实长任务再加 `--force`。
4. **多语检索**：`search()` 把查询词过**中→英词典**展开成源语言关键词再匹配。
5. **本体驱动的建议**：`recommend()` = 候选(**共享 slug** 的本体泛化) + 约束(`must_have`) + 打分(共享数) + 可解释(返回共享关系)。

## 如何照搬到你的书 / How to adapt

1. **换 P1**：把 `structure()` 换成对你源的解析（EPUB/HTML 用语义 class；扫描件先 OCR）。
   对象模型保持 `{id, title, parts[], rels[]}` 形状。
2. **换 P2 词表**：把你领域的封闭词（动作/工具/单位/状态）填入 `Vocabulary`，给足别名 + 中英名。
   开放字段（从正文抽"做了什么/参数多少"）用 LLM 抽取后**再过 `normalize()` 与校验**。
3. **换 P3 存储**：把 `:memory:` 换成 SQLite 文件路径（本项目 `output/foodlab.sqlite3`）；
   需要多层语义推理时，把 relations 迁到 RDF/图库，schema 形状不变。
4. **换 P4 应用**：`query/search/analysis/recommend` 就是 API 层，直接接你的 Web/CLI。
5. **补 P5/P6**：覆盖率 + 抽检 + 可溯源；编排（缓存/续跑）+ 一键脚本。

## 局限 / Limits（这是骨架，不是成品）

- `normalize()` 的开放域抽取在 demo 里用简单匹配；真实场景**用 LLM 抽**（见 `llm_extract.py` 的提示词模板）。
- `recommend()` 只演示"内容型 + 规则 + 打分"，未接协同过滤/用户画像。
- 未做推理层（无 OWL/图推理）；需要时再引入。

> 完整方法论见 [`../METHODOLOGY.md`](../METHODOLOGY.md)。
