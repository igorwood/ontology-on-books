# 迁移清单 / Migration checklist

> 把本 playbook 用到**一本新的应用型书**时，按序勾选。
> Step-by-step checklist to apply this playbook to a new applied/instructional book.

## 0. 准备 / Prep
- [ ] 复制本包：`cp -r ontology_playbook/ /path/to/new-project/`
- [ ] 判定源类型：**结构化**（EPUB/HTML）还是**扫描件**（PDF 图像）→ 决定 P0 路线
- [ ] 写清**要回答的问题**（决定 schema）：query / search / analysis / recommend 各举 ≥2 例

## 1. 领域建模 / Domain modeling
- [ ] 定义实体对象模型：`{id, title, parts[], attrs}`
- [ ] 列出部件类型（如 ingredients / steps / tools / warnings）
- [ ] 建立**受控词表**（封闭域：动作 / 工具 / 单位 / 状态），每项含 `en / zh / aliases`

## 2. 解析 + 结构抽取 / Parse + Structure（P0·P1）
- [ ] 结构化源：按语义 class / 锚点 / 标题层级**确定性**解析 → JSON
- [ ] 扫描源：先 OCR / 版面分析，再抽
- [ ] 产出**全文 Markdown**（保真 + 审计底稿）
- [ ] 抽查对象边界（标题/分组/续行合并是否正确）

## 3. 归一 / Normalize（P2）
- [ ] 自由文本（动作/工具）经 `Vocabulary.normalize()` 归一
- [ ] 开放字段（"做了什么 / 参数多少"）用 **LLM 抽** → 过 `normalize()` + 校验
- [ ] 记录未命中 slug → 增量扩词表 → **重跑**（续跑）
- [ ] （可选）多语：查询词典 zh → 源语言

## 4. 入库 / Store（P3）
- [ ] 最小 schema：实体 / 部件 / 词表 / 关系 / 状态
- [ ] 保序用 `ord`；幂等 upsert；`status` 断点续跑
- [ ] 需要多层语义推理时，再把 relations 迁到 RDF / 图库

## 5. 应用 / Apply（P4）
- [ ] `query`：按词表反查
- [ ] `search`：多字段 + 多语
- [ ] `analysis`：聚合 / 共现
- [ ] `recommend`：本体泛化 + 约束 + 打分 + **可解释**

## 6. 验收 / Validate（P5）
- [ ] 结构覆盖率（应得 vs 实得对象）
- [ ] 归一命中率 / 词表缺口量化
- [ ] 可溯源率（断言能回原书）
- [ ] 数字/参数走**确定性校验**（白名单 + 量纲 + 区间）
- [ ] 高风险字段人工抽检

## 7. 运维 / Operate（P6）
- [ ] 编排：缓存 / 血缘 / 断点续跑
- [ ] 一键脚本：start / status / stop / restart
- [ ] 成本档位：按任务难度选模型；批量 + 并发上限 + 缓存
- [ ] RUNBOOK：记录**本机实测的坑**（端口/编码/HOME/注解限制…）

## 8. 完成定义 / Definition of done
- [ ] demo 换成真实数据跑通
- [ ] 四类能力各有可演示的例子
- [ ] 包内未残留原项目路径（`grep -rn "docs/\|pipeline/" ontology_playbook/` 应为空）
- [ ] 图（`workflow.mmd` / `.png`）可离线查看

> 关联 / see also：[`METHODOLOGY.md`](METHODOLOGY.md)（方法论）、[`scaffold/README.md`](scaffold/README.md)（如何照搬）。
