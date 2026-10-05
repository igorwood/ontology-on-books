"""应用型书籍 → 本体驱动系统 · 可复用脚手架 / Reusable scaffold.

把 cuisine_lab 验证过的模式抽象成最小骨架，四阶段 + 四能力，纯标准库、可直接运行：

    python scaffold/ontology_scaffold.py

四阶段 / stages
  P1 structure(source)  → 领域对象（entity + parts）          —— 用源标记确定性抽取
  P2 normalize(objects) → 归一（受控词表：别名 / 最长子串匹配）
  P3 store(objects)      → SQLite 最小 schema（实体/部件/词表/关系/状态）
  P4 apply()             → query / search / analysis / recommend

复用本项目验证过的模式：
  - 受控词表归一（{id,en,zh,aliases} + 最长子串）
  - 双列联 schema（实体–部件–词表–关系–状态）
  - 状态表 + 跳过已完成（断点续跑）
  - 多语检索（查询词过词典展开成源语言关键词）
  - 建议 = 本体泛化(同 slug) + 约束过滤 + 打分
"""
from __future__ import annotations

import re
import sqlite3

# ── P2 受控词表 / Controlled vocabulary ───────────────────────────────
class Vocabulary:
    """{slug: {en, zh, kind, aliases[]}} + 别名索引（最长子串优先）。"""

    def __init__(self, entries: list[dict]):
        self.by_slug = {e["slug"]: e for e in entries}
        idx = {}
        for e in entries:
            for a in [e["en"]] + e.get("aliases", []):
                idx[a.lower()] = e["slug"]
        self._idx = idx
        self._sorted = sorted(idx, key=len, reverse=True)  # 长别名优先

    def normalize(self, text: str) -> str | None:
        t = (text or "").strip().lower()
        if not t:
            return None
        if t in self._idx:
            return self._idx[t]
        for a in self._sorted:
            if re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", t):
                return self._idx[a]
        return None

    def label(self, slug: str, lang: str = "zh") -> str:
        e = self.by_slug.get(slug)
        return (e.get(lang) or e.get("en") or slug) if e else slug


# ── P1 结构抽取 / Structure （按源标记确定性抽取；此处用内联样例）──────
def structure(source: list[dict]) -> list[dict]:
    """真实场景：解析 EPUB/HTML 的语义 class/锚点。这里用样例字典演示形状。
    对象模型 / object model: {id, title, ingredients[], steps[], equipment[], kind_hint}"""
    return source


# ── P2 归一 / Normalize ───────────────────────────────────────────────
def normalize(objects: list[dict], vocab: Vocabulary) -> list[dict]:
    """把开放文本（食材/设备/工艺）归一到 slug；未命中的保留 None（可增量扩表）。"""
    for o in objects:
        o["rels"] = []  # [(kind, slug)]
        for text in o.get("equipment", []):
            s = vocab.normalize(text)
            if s:
                o["rels"].append(("equipment", s))
        for text in o.get("steps", []):
            s = vocab.normalize(text)          # 真实场景用 LLM 抽动词/参数后归一
            if s:
                o["rels"].append(("process", s))
    return objects


# ── P3 入库 / Store （最小 schema）────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY, title TEXT, kind TEXT);
CREATE TABLE IF NOT EXISTS parts(id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id TEXT, kind TEXT, ord INTEGER, text TEXT);
CREATE TABLE IF NOT EXISTS vocab(slug TEXT PRIMARY KEY, en TEXT, zh TEXT, kind TEXT);
CREATE TABLE IF NOT EXISTS relations(entity_id TEXT, kind TEXT, slug TEXT);
CREATE TABLE IF NOT EXISTS status(entity_id TEXT PRIMARY KEY, status TEXT);
CREATE INDEX IF NOT EXISTS ix_rel ON relations(slug);
"""


def store(objects: list[dict], vocab: Vocabulary) -> sqlite3.Connection:
    """幂等建库：已 status='ok' 的实体跳过（断点续跑）。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    done = {r["entity_id"] for r in conn.execute("SELECT entity_id FROM status WHERE status='ok'")}
    conn.executemany("INSERT OR IGNORE INTO vocab(slug,en,zh,kind) VALUES(?,?,?,?)",
                     [(e["slug"], e["en"], e.get("zh", ""), e.get("kind", ""))
                      for e in vocab.by_slug.values()])
    for o in objects:
        if o["id"] in done:
            continue
        conn.execute("INSERT OR REPLACE INTO entities(id,title,kind) VALUES(?,?,?)",
                     (o["id"], o["title"], o.get("kind", "")))
        for i, t in enumerate(o.get("ingredients", [])):
            conn.execute("INSERT INTO parts(entity_id,kind,ord,text) VALUES(?,?,?,?)",
                         (o["id"], "ingredient", i, t))
        for kind, slug in o.get("rels", []):
            conn.execute("INSERT INTO relations(entity_id,kind,slug) VALUES(?,?,?)",
                         (o["id"], kind, slug))
        conn.execute("INSERT OR REPLACE INTO status(entity_id,status) VALUES(?,'ok')", (o["id"],))
    conn.commit()
    return conn


# ── P4 应用 / Apply ───────────────────────────────────────────────────
def query(conn, slug: str) -> list[str]:
    """按受控词表反查 / reverse lookup by vocab slug. 例：用铸铁煎锅的菜。"""
    return [r["title"] for r in conn.execute(
        "SELECT DISTINCT e.title FROM relations r JOIN entities e ON e.id=r.entity_id"
        " WHERE r.slug=? ORDER BY e.title", (slug,))]


def search(conn, q: str, lexicon: dict[str, list[str]]) -> list[str]:
    """多语多字段检索 / multilingual search：q 过中→英词典扩展后匹配 标题/部件/关系。"""
    terms = [q] + [t for t in lexicon.get(q.strip().lower(), []) if t != q]
    likes = " OR ".join(["lower(e.title) LIKE ?"] * len(terms)
                        + ["lower(p.text) LIKE ?"] * len(terms))
    params = [f"%{t.lower()}%" for t in terms] * 2
    return [r["title"] for r in conn.execute(
        f"SELECT DISTINCT e.title FROM entities e LEFT JOIN parts p ON p.entity_id=e.id"
        f" WHERE {likes} ORDER BY e.title", params)]


def analysis(conn) -> list[tuple]:
    """聚合分析 / aggregation：受控词表使用频次。"""
    return [(r["slug"], r["c"]) for r in conn.execute(
        "SELECT slug, COUNT(DISTINCT entity_id) c FROM relations GROUP BY slug ORDER BY c DESC")]


def recommend(conn, entity_id: str, must_have: set[str] | None = None) -> list[tuple]:
    """本体驱动的建议 / ontology-driven recommend：
       候选=共享同一 slug（本体泛化）；约束=必须满足 must_have；打分=共享 slug 数。"""
    mine = {r["slug"] for r in conn.execute("SELECT slug FROM relations WHERE entity_id=?", (entity_id,))}
    scores: dict[str, int] = {}
    for row in conn.execute("SELECT entity_id, slug FROM relations WHERE entity_id!=?", (entity_id,)):
        scores[row["entity_id"]] = scores.get(row["entity_id"], 0) + (1 if row["slug"] in mine else 0)
    cand = []
    for eid, sc in sorted(scores.items(), key=lambda x: -x[1]):
        if not sc:
            continue
        slugs = {r["slug"] for r in conn.execute("SELECT slug FROM relations WHERE entity_id=?", (eid,))}
        if must_have and not must_have.issubset(slugs):
            continue
        title = conn.execute("SELECT title FROM entities WHERE id=?", (eid,)).fetchone()["title"]
        cand.append((title, sc, sorted(slugs & mine)))
    return cand


# ── 演示 / Demo ───────────────────────────────────────────────────────
def main() -> None:
    vocab = Vocabulary([
        {"slug": "sear", "en": "sear", "zh": "煎封上色", "kind": "process",
         "aliases": ["pan-sear", "pan searing", "pan-searing", "sizzle"]},
        {"slug": "rest", "en": "rest", "zh": "静置", "kind": "process", "aliases": ["resting"]},
        {"slug": "simmer", "en": "simmer", "zh": "小火慢煮", "kind": "process", "aliases": ["simmering"]},
        {"slug": "cast_iron_skillet", "en": "cast-iron skillet", "zh": "铸铁煎锅",
         "kind": "equipment", "aliases": ["cast iron skillet", "skillet"]},
        {"slug": "saucepan", "en": "saucepan", "zh": "单柄汤锅", "kind": "equipment", "aliases": []},
    ])
    lexicon = {"番茄": ["tomato"], "牛肉": ["beef"], "煎": ["sear"]}

    source = [
        {"id": "r1", "title": "Pan-Seared Steak", "ingredients": ["2 ribeye steaks", "salt", "butter"],
         "equipment": ["cast-iron skillet", "tongs"], "steps": ["Sear the steaks hard.", "Let rest 5 min."]},
        {"id": "r2", "title": "Pan-Seared Pork Chops", "ingredients": ["4 pork chops", "salt"],
         "equipment": ["cast-iron skillet"], "steps": ["Sear both sides.", "Rest before slicing."]},
        {"id": "r3", "title": "Quick Tomato Pasta", "ingredients": ["1 can tomato", "pasta", "oil"],
         "equipment": ["saucepan"], "steps": ["Simmer the sauce."]},
    ]
    objs = normalize(structure(source), vocab)
    conn = store(objs, vocab)

    print("归一 / normalize:", "pan-searing ->", vocab.normalize("pan-searing"))
    print("查询 / query 铸铁煎锅:", query(conn, "cast_iron_skillet"))
    print("搜索 / search 番茄(zh):", search(conn, "番茄", lexicon))
    print("分析 / analysis top:", analysis(conn)[:4])
    print("建议 / recommend r1 ->", recommend(conn, "r1"))


if __name__ == "__main__":
    main()
