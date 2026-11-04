"""第 5 章 业务数据分析 · 银行理财产品销售 KPI 的 Python 复现

教材原做法
----------
第 5 章用 Power BI「案例结果.pbix」做银行理财产品销售的 KPI 看板：
风险偏好（S1–S5）× 产品类别 × 客户收入段 × 年龄段，配合切片器切「是否盈利」。
度量值大多形如：

    DAX: 销售额 = SUM(bank_sales[amount])
    DAX: 盈利客户占比 = DIVIDE(CALCULATE(COUNTROWS(bank_sales), bank_sales[profit] > 0),
                             COUNTROWS(bank_sales))
    DAX: 同比 = DIVIDE([本期] - [上期], [上期])

迁移思路
--------
DAX 的 CALCULATE 本质是「先改筛选上下文，再聚合」，对应 pandas 的
「先构造布尔掩码，再 groupby / 聚合」。切片器联动 = 把筛选条件做成函数参数。

运行：python scripts/ch05_bank_kpi.py
输出：outputs/ch05_*.csv、outputs/ch05_*.png
"""
from __future__ import annotations

import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch05")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
C_MAIN, C_ALT, C_GREEN, C_GRAY = "#4472C4", "#ED7D31", "#70AD47", "#A5A5A5"
GRID = "#E1E4E8"

INCOME_ORDER = ["5万以下", "5万-10万", "10万-20万", "20万-50万",
                "50万-100万", "100万以上"]
AGE_ORDER = ["18-30岁", "31-40岁", "41-50岁", "50-60岁", "61岁以上"]


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    sales = pd.read_csv(os.path.join(DATA, "bank_sales.csv"))
    risk = pd.read_csv(os.path.join(DATA, "bank_risk.csv"))
    cat = pd.read_csv(os.path.join(DATA, "bank_category.csv"))
    edu = pd.read_csv(os.path.join(DATA, "bank_edu.csv"))

    df = (sales
          .merge(risk, on="risk_code", how="left")
          .merge(cat, on="cat_code", how="left")
          .merge(edu, on="edu_code", how="left"))
    df["盈利"] = df["profit"] > 0
    df["利润率%"] = (df["profit"] / df["amount"] * 100).round(2)
    return df, risk


def kpi(df: pd.DataFrame) -> pd.DataFrame:
    """看板顶部的 KPI 卡：销售额、笔数、客单价、盈利客户占比、平均利润率。"""
    rows = [
        ("销售总额（元）", f"{df['amount'].sum():,.0f}"),
        ("成交笔数", f"{len(df):,}"),
        ("客单价（元）", f"{df['amount'].mean():,.0f}"),
        ("盈利笔数占比", f"{df['盈利'].mean():.2%}"),
        ("平均利润率", f"{df['利润率%'].mean():.2f}%"),
        ("总利润（元）", f"{df['profit'].sum():,.0f}"),
    ]
    out = pd.DataFrame(rows, columns=["指标", "数值"])
    print("\n[1] KPI 汇总（教材看板顶部卡片）")
    print(out.to_string(index=False))
    return out


def by_risk(df: pd.DataFrame) -> pd.DataFrame:
    """风险等级 × 盈利：DAX 的 CALCULATE(..., profit>0) 写成布尔掩码。"""
    g = (df.groupby(["risk_code", "risk_desc"], dropna=False)
         .agg(笔数=("amount", "size"), 销售额=("amount", "sum"),
              利润=("profit", "sum"), 平均金额=("amount", "mean"))
         .reset_index())
    win = df[df["盈利"]].groupby("risk_code")["amount"].size().rename("盈利笔数")
    g = g.merge(win, on="risk_code", how="left").fillna({"盈利笔数": 0})
    g["盈利笔数占比%"] = (g["盈利笔数"] / g["笔数"] * 100).round(2)
    g["销售额占比%"] = (g["销售额"] / g["销售额"].sum() * 100).round(2)
    print("\n[2] 风险等级 × 盈利（教材切片器「风险偏好」）")
    print(g.round(0).to_string(index=False))
    return g


def by_income_age(df: pd.DataFrame):
    """收入段 × 年龄段交叉：教材用矩阵表看「哪类客户买得多、谁在亏」。"""
    d = df.assign(收入段=df["income"].where(df["income"].isin(INCOME_ORDER)),
                  年龄段=df["age_band"].where(df["age_band"].isin(AGE_ORDER)))

    income = (d.groupby("收入段", dropna=True)
              .agg(笔数=("amount", "size"), 销售额=("amount", "sum"),
                   平均金额=("amount", "mean"), 平均利润率=("利润率%", "mean"))
              .reindex(INCOME_ORDER).reset_index())
    age = (d.groupby("年龄段", dropna=True)
           .agg(笔数=("amount", "size"), 销售额=("amount", "sum"),
                平均金额=("amount", "mean"), 平均利润率=("利润率%", "mean"))
           .reindex(AGE_ORDER).reset_index())

    cross = pd.pivot_table(d.dropna(subset=["收入段", "年龄段"]),
                           index="收入段", columns="年龄段", values="amount",
                           aggfunc="sum", fill_value=0.0).reindex(INCOME_ORDER)
    cross.columns = [f"{c} 销售额" for c in cross.columns]

    print("\n[3] 收入段 / 年龄段的销售额与利润率")
    print(income.round(1).to_string(index=False))
    print(age.round(1).to_string(index=False))
    print("\n[3b] 收入段 × 年龄段 销售额交叉表")
    print(cross.round(0).to_string())
    return income, age, cross


def by_purpose(df: pd.DataFrame) -> pd.DataFrame:
    """购买用途与原因：教材里用条形图看客户诉求。"""
    p = (df.groupby("purpose")
         .agg(笔数=("amount", "size"), 销售额=("amount", "sum"))
         .reset_index().sort_values("销售额", ascending=False))
    p["销售额占比%"] = (p["销售额"] / p["销售额"].sum() * 100).round(2)
    print("\n[4] 购买目的分布")
    print(p.round(0).to_string(index=False))
    return p


def plot(df, risk: pd.DataFrame, income: pd.DataFrame, age: pd.DataFrame,
         purpose: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), dpi=150)

    a = axes[0][0]
    r = risk
    a.bar(r["risk_code"], r["销售额"] / 1e4, color=C_MAIN)
    for i, (v, w) in enumerate(zip(r["销售额"] / 1e4, r["盈利笔数占比%"])):
        a.text(i, v, f"{v:.0f}万\n盈利{w:.0f}%", ha="center", va="bottom", fontsize=8)
    a.set_title("各风险等级销售额（万元）", fontsize=10.5)
    a.set_ylim(0, (r["销售额"] / 1e4).max() * 1.28)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    a = axes[0][1]
    a.barh(income["收入段"][::-1], income["平均金额"][::-1], color=C_ALT)
    for i, v in enumerate(income["平均金额"][::-1]):
        a.text(v, i, f" {v:,.0f}", va="center", fontsize=8.5)
    a.set_title("各收入段客单价（元）", fontsize=10.5)
    a.grid(axis="x", color=GRID)
    a.set_axisbelow(True)

    a = axes[1][0]
    a.bar(age["年龄段"], age["平均利润率"], color=C_GREEN)
    a.axhline(df["利润率%"].mean(), color=C_ALT, ls="--", lw=1.3,
              label=f"整体 {df['利润率%'].mean():.1f}%")
    for i, v in enumerate(age["平均利润率"]):
        a.text(i, v, f"{v:.1f}%", ha="center",
               va="bottom" if v >= 0 else "top", fontsize=8.5)
    a.set_title("各年龄段平均利润率", fontsize=10.5)
    a.tick_params(axis="x", rotation=12)
    a.legend(fontsize=8.5)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    a = axes[1][1]
    p = purpose.head(6)
    a.barh(p["purpose"][::-1], p["销售额"][::-1] / 1e4, color=C_GRAY)
    a.set_title("购买目的 Top6（万元）", fontsize=10.5)
    a.grid(axis="x", color=GRID)
    a.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(OUT, "ch05_bank_kpi.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\n    图 → {os.path.relpath(path, ROOT)}")


def main() -> int:
    print("=" * 78)
    print("第 5 章 · 银行理财产品销售 KPI（Power BI 看板 → pandas）")
    print("=" * 78)
    df, _ = load()
    print(f"\n数据：{len(df)} 笔成交，{df['risk_code'].nunique()} 个风险等级，"
          f"{df['cat_code'].nunique()} 类产品，缺失率 {df.isna().mean().mean():.2%}")
    k = kpi(df)
    risk = by_risk(df)
    income, age, cross = by_income_age(df)
    purpose = by_purpose(df)
    plot(df, risk, income, age, purpose)

    for name, d in (("kpi", k), ("risk", risk), ("income", income),
                    ("purpose", purpose),
                    ("age", age), ("cross", cross.reset_index())):
        path = os.path.join(OUT, f"ch05_{name}.csv")
        d.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  → {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
