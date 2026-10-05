# Ontology Playbook · 应用型书籍 → 本体驱动系统

> **自包含、可整体搬运**的方法论与脚手架包。
> A self-contained, portable playbook: turn an applied/instructional book into a
> query / search / analysis / recommendation system.
>
> 直接 `cp -r ontology_playbook/ /path/to/other-project/` 即可迁移，包内无对外依赖。

---

## 目录 / Contents

```
ontology_playbook/
├── README.md                    本文件：入口 + 迁移说明 / entry & how to port
├── METHODOLOGY.md               方法论全文（六阶段工作流 + 原则/决策/模式/反模式）
├── TEMPLATE_CHECKLIST.md        迁移到新书的逐步勾选清单 / migration checklist
├── workflow.mmd                 六阶段工作流 Mermaid 图源
├── workflow.dot / .png / .svg   同一图的 Graphviz 源 + 离线位图/矢量图
└── scaffold/
    ├── ontology_scaffold.py     可复用骨架（四阶段 + 四能力，纯 stdlib，可运行 demo）
    └── README.md                脚手架说明与"如何照搬"
```

关系 / relation：`METHODOLOGY.md` 讲**为什么与怎么做**；`scaffold/` 给**能跑的骨架**；
`workflow.mmd` 是配图。三者自洽，不依赖任何具体项目。

---

## 快速开始 / Quick start

```bash
# 1) 读方法 / read the method
less METHODOLOGY.md

# 2) 跑骨架 demo（无需安装）/ run the scaffold demo (no deps)
python3 scaffold/ontology_scaffold.py

# 3) 图：离线位图已内置（workflow.png / workflow.svg）
#    重渲染 / re-render：
dot -Tpng workflow.dot -o workflow.png       # Graphviz（离线，推荐）
# 或（需浏览器）/ or (needs a browser):
npx -y @mermaid-js/mermaid-cli -i workflow.mmd -o workflow.png
# 注：macOS 沙箱下无头 Chrome 会硬写 ~/Library 而失败 → 优先用 graphviz dot。
# Note: headless Chrome writes ~/Library and fails under macOS sandbox → prefer dot.
```

---

## 迁移到其他项目 / How to port

把整个 `ontology_playbook/` 复制到目标项目，然后按字段替换四处：

| 位置 | 通用骨架 | 你要换成 |
|---|---|---|
| P1 结构抽取 | `scaffold/ontology_scaffold.py` 的 `structure()` | 对你源（EPUB/HTML/PDF）的解析；保持对象形状 `{id,title,parts[],rels[]}` |
| P2 词表 | `Vocabulary([...])` 示例 | 你领域的封闭词（动作/工具/单位/状态）+ 别名 + 中英名 |
| P2 抽取 | demo 里 `normalize()` 的简单匹配 | **用 LLM 抽开放字段**（"做了什么/参数多少"）后过 `normalize()` + 校验 |
| P3 存储 | `store(":memory:")` | 换成持久化路径（SQLite 文件；需要多层推理再上 RDF/图） |
| P4 应用 | `query/search/analysis/recommend` | 直接接你的 Web/CLI |

**保持不变的五个模式**（这是本 playbook 的核心资产）：
1. 受控词表归一（精确 → 最长子串 → None）
2. 双列联 schema（实体 / 部件 / 词表 / 关系 / 状态）
3. 状态表 + 断点续跑
4. 多语检索（查询词过词典展开）
5. 本体驱动建议（泛化 + 约束 + 打分 + 可解释）

---

## 依赖 / Dependencies

- 骨架与 demo：**Python 3 标准库**（`re`、`sqlite3`），零依赖。
- 生产化时按需引入：LLM 客户端（抽取/翻译）、Web 框架或 stdlib `http.server`、可选 RDF/图库。

---

## 来源与边界 / Origin & limits

- 抽象自 `cuisine_lab`（The Food Lab EPUB）的实操经验；已**去项目化**，可独立使用。
- 边界：`recommend()` 为内容型 + 规则演示，未接协同过滤；未内置推理层（无 OWL/图推理）；
  归一覆盖率取决于词表维护。详见 `METHODOLOGY.md` §7。

> 版本 / version：playbook v1（2026-10）。迁移后请按你的领域替换词表并重跑归一。
