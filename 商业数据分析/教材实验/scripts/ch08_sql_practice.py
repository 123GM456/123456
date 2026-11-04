"""第 8 章 SQL 语言基础与 MySQL 入门 · 用 sqlite3 跑教材语句

教材原做法
----------
第 8 章配套 `SQL基础语法.sql`（约 200 行），全部针对 MySQL 里的 `kdd99` 库，
覆盖：SELECT/WHERE/ORDER BY、表达式造新列、聚合与 GROUP BY、多表 JOIN、
子查询、CASE WHEN、开窗函数（配套 `MySQL8.0开窗函数.pdf`）。

迁移思路
--------
本机没有 MySQL 服务，但 sqlite3 是 Python 标准库，语法覆盖了教材 90% 的语句。
两者差异集中在这几处，脚本里用一个 `to_sqlite()` 做适配：

| MySQL                        | sqlite3                                   |
|------------------------------|-------------------------------------------|
| `库名.表名`（kdd99.xxx）     | 没有库概念，直接 `xxx_table`              |
| `datediff(a, b)`             | `CAST(julianday(a) - julianday(b) AS INT)`|
| `DATE_FORMAT(d, '%Y-%m')`    | `strftime('%Y-%m', d)`                    |
| `LIMIT n, m`                 | `LIMIT m OFFSET n`                        |
| `IFNULL` / `IF`              | `IFNULL` 可用，`IF` 要换 `CASE WHEN`      |
| 窗口函数（8.0+）             | sqlite 3.25+ 支持，语法一致               |

运行：python scripts/ch08_sql_practice.py
输出：outputs/ch08_*.csv、outputs/kdd99.db、outputs/ch08_result.txt
"""
from __future__ import annotations

import os
import re
import sqlite3

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch01")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)
DB = os.path.join(OUT, "kdd99.db")

# 教材表名 → 本地 csv
TABLES = {
    "kdd99_trans": "trans",
    "kdd99_accounts": "accounts",
    "kdd99_disp": "disp",
    "kdd99_clients": "clients",
    "kdd99_card": "card",
    "kdd99_loans": "loans",
    "kdd99_order": "order",
    "kdd99_district": "district",
    "sale": "sale",
}


def coerce_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """原 csv 里数值列带引号，sqlite 会当文本比较（'999' < '10000' 为 False）。
    这里把"看起来是数字"的列转成数值，否则 CASE WHEN 分箱和 SUM 都会算错。"""
    out = df.copy()
    for col in out.columns:
        # 注意：pandas 3.0 里字符串列的 dtype 变成了 "str"（不是 object），
        # 所以这里用"不是数值类型"来判断，而不是 `dtype == object`。
        if pd.api.types.is_numeric_dtype(out[col]):
            continue
        # 原表金额带千分位（"1,200"），先去掉逗号再转数值
        cleaned = out[col].astype(str).str.replace(",", "", regex=False).str.strip()
        conv = pd.to_numeric(cleaned, errors="coerce")
        if conv.notna().mean() >= 0.8:
            out[col] = conv
    return out


def build_db() -> sqlite3.Connection:
    """把 8 张 csv + sale 灌进 sqlite，表名沿用教材（去掉 kdd99. 前缀）。"""
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    for table, csv_name in TABLES.items():
        path = os.path.join(DATA, f"{csv_name}.csv")
        df = coerce_numbers(pd.read_csv(path))
        df.to_sql(table, con, index=False)
        print(f"  {table:<16} ← {os.path.basename(path):<14} {len(df):>8,} 行")
    return con


def to_sqlite(sql: str) -> str:
    """把教材里的 MySQL 方言改写成 sqlite 能吃的样子。"""
    s = sql
    s = re.sub(r"\bkdd99\.", "", s, flags=re.I)                     # 去库名前缀
    s = re.sub(r"datediff\(\s*([^,]+?)\s*,\s*([^)]+?)\)",
               r"CAST(julianday(\1) - julianday(\2) AS INT)", s, flags=re.I)
    s = re.sub(r"if\((.+?),", lambda m: "CASE WHEN " + m.group(1) + " THEN", s,
               flags=re.I)
    s = re.sub(r"\bIF\s*\(", lambda m: "CASE_IF(", s)               # 复杂的 IF 交给手写
    return s


# 教材语句精选：每条都标注了它在教材里属于哪一节
QUERIES = [
    ("8.2 选择列与排序（教材 SQL2）",
     "select year, market, sale, profit from sale order by year, market"),
    ("8.2 去重（DISTINCT）",
     "select distinct year from sale order by year"),
    ("8.2 条件过滤 + BETWEEN + 排序",
     """select account_id, date, bank, amount
        from kdd99_trans
        where date between '1999-01-01' and '1999-01-31'
          and k_symbol = '房屋贷款'
        order by date, account_id"""),
    ("8.3 表达式创建新列",
     "select year, sale, profit, profit / sale as rate from sale where sale > 0"),
    ("8.4 聚合函数",
     """select count(*) as 笔数, sum(amount) as 交易总额,
               round(avg(amount), 2) as 平均金额, max(amount) as 最大单笔
        from kdd99_trans"""),
    ("8.4 GROUP BY + HAVING",
     """select type, count(*) as 笔数, round(sum(amount), 0) as 金额
        from kdd99_trans group by type
        having count(*) > 1000 order by 笔数 desc"""),
    ("8.5 多表 JOIN（客户画像常用三表连接）",
     """select count(*) as 成交卡数, round(avg(t.amount), 2) as 平均交易额
        from kdd99_trans t
        join kdd99_accounts a on t.account_id = a.account_id
        join kdd99_district d on a.district_id = d.district_id
        where d.urban_ratio > 0.6"""),
    ("8.6 子查询：高于平均金额的交易",
     """select count(*) as 笔数 from kdd99_trans
        where amount > (select avg(amount) from kdd99_trans)"""),
    ("8.7 CASE WHEN 分箱（教材「用表达式分箱」）",
     """select case when amount < 1000 then '小额(<1千)'
                    when amount < 10000 then '中额(1千-1万)'
                    else '大额(≥1万)' end as 金额区间,
               count(*) as 笔数
        from kdd99_trans group by 金额区间 order by 笔数 desc"""),
    ("8.8 开窗函数：每个地区的交易额排名",
     """select district_id, 交易额,
               rank() over (order by 交易额 desc) as 排名
        from (select a.district_id, sum(t.amount) as 交易额
                from kdd99_trans t join kdd99_accounts a
                  on t.account_id = a.account_id
               group by a.district_id)
        limit 10"""),
]


def pandas_equivalents() -> None:
    """把两条 SQL 用 pandas 再写一遍，验证结果一致（SQL ↔ pandas 对照学习法的核心）。"""
    trans = pd.read_csv(os.path.join(DATA, "trans.csv"))
    accounts = pd.read_csv(os.path.join(DATA, "accounts.csv"))
    district = pd.read_csv(os.path.join(DATA, "district.csv"))
    district["urban_ratio"] = pd.to_numeric(district["urban_ratio"], errors="coerce")
    trans["amount"] = pd.to_numeric(trans["amount"], errors="coerce")

    print("\n" + "=" * 78)
    print("SQL ↔ pandas 对照（同样的两个问题各写两遍）")
    print("=" * 78)

    # ① GROUP BY + HAVING
    g = (trans.groupby("type", dropna=True)
         .agg(笔数=("amount", "size"), 金额=("amount", "sum"))
         .reset_index())
    g = g[g["笔数"] > 1000].sort_values("笔数", ascending=False)
    print("\n[对照 1] 按交易类型分组、笔数 > 1000（等价于 GROUP BY ... HAVING）")
    print(g.assign(金额=g["金额"].round(0)).to_string(index=False))

    # ② 三表 JOIN + 条件过滤
    m = (trans.merge(accounts[["account_id", "district_id"]], on="account_id", how="inner")
              .merge(district[["district_id", "urban_ratio"]], on="district_id", how="inner"))
    urban = m[m["urban_ratio"] > 0.6]
    print(f"\n[对照 2] 城市化率 > 0.6 的地区：{len(urban):,} 笔交易，"
          f"平均金额 {urban['amount'].mean():,.2f}（等价于两表 JOIN + WHERE）")


def main() -> int:
    print("=" * 78)
    print("第 8 章 · SQL 基础语法（MySQL → sqlite3）")
    print("=" * 78)
    print("\n建库：outputs/kdd99.db")
    con = build_db()

    lines = []
    for i, (title, sql) in enumerate(QUERIES, 1):
        adapted = to_sqlite(sql)
        try:
            df = pd.read_sql_query(adapted, con)
        except Exception as exc:                    # noqa: BLE001
            print(f"\n[{i}] {title}\n    执行失败：{exc}")
            lines.append(f"[{i}] {title}\nFAILED: {exc}\n")
            continue
        print(f"\n[{i}] {title}")
        print(f"    返回 {len(df)} 行")
        print(df.head(5).to_string(index=False))
        name = f"ch08_q{i:02d}"
        df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False, encoding="utf-8-sig")
        lines.append(f"[{i}] {title}\n{adapted}\n→ {len(df)} 行\n"
                     f"{df.head(10).to_string(index=False)}\n")

    pandas_equivalents()

    with open(os.path.join(OUT, "ch08_result.txt"), "w", encoding="utf-8") as f:
        f.write("第 8 章 SQL 语句执行记录（sqlite3 方言适配后）\n\n")
        f.write("\n".join(lines))
    print(f"\n执行记录 → outputs/ch08_result.txt")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
