"""第 1 章 数据分析思维 · 关系模型与维度模型的 Python 复现

教材原做法
----------
第 1 章用 Power BI 的「关系视图」把 8 张表拖到一起连成关系模型，再用「维度模型」
视图演示商场销售数据表（事实表 + 维表）。Power BI 里这步是鼠标连线，看不见 SQL。

迁移思路
--------
关系模型在关系数据库里就是主键/外键；在 pandas 里就是 `merge`。
本脚本做三件事：
1) 打印每张表的主键、行数、字段，说明「谁连谁」；
2) 用 merge 依次还原教材里那套 star schema（事实表 trans + 维表 accounts/clients/district）；
3) 在这个星型模型上跑教材的 4 个问题：按地区、按性别年龄、按账户频率、按贷款状态。

运行：python scripts/ch01_data_model.py
输出：outputs/ch01_*.csv、outputs/ch01_schema.png
"""
from __future__ import annotations

import os

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch01")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 教材 8 张表的主键与业务含义（等价于 Power BI 关系视图里的连线端点）
SCHEMA = {
    "clients": ("client_id", "客户：性别、出生日期、所在地区"),
    "accounts": ("account_id", "账户：开立地区、对账单频率、开户日期"),
    "disp": ("disp_id", "客户-账户关系（多对多桥表）"),
    "card": ("card_id", "银行卡：发卡日期、卡类型"),
    "loans": ("loan_id", "贷款：金额、期限、月供、状态"),
    "order": ("order_id", "汇款指令：收款行、金额"),
    "trans": ("trans_id", "交易流水（事实表）：类型、金额、余额"),
    "district": ("district_id", "地区维表：人口、平均工资、失业率、犯罪率"),
}


def load() -> dict[str, pd.DataFrame]:
    """读入 8 张表。教材的原始 csv 是 GBK 且数值列带引号，统一在这里做类型归一。"""
    tables = {}
    for name in SCHEMA:
        tables[name] = pd.read_csv(
            os.path.join(DATA, f"{name}.csv"), low_memory=False)
    # 数值列强制转换：CSV 里 population/avg_salary 等是带引号的字符串
    num_cols = ["population", "avg_salary", "n_cities", "urban_ratio",
                "unemp_95", "unemp_96", "crime_96", "crime_95", "n_ent"]
    district = tables["district"]
    for col in num_cols:
        if col in district.columns:
            district[col] = pd.to_numeric(district[col], errors="coerce")
    for col in ("amount", "balance"):
        for name in ("trans", "loans", "order"):
            if col in tables[name].columns:
                tables[name][col] = pd.to_numeric(tables[name][col], errors="coerce")
    return tables


def show_schema(tables: dict[str, pd.DataFrame]) -> None:
    print("=" * 78)
    print("一、关系模型：8 张表的主键与外键（教材 Power BI「关系视图」）")
    print("=" * 78)
    print(f"{'表名':<10}{'行数':>7}  {'主键':<12}{'业务含义'}")
    for name, (pk, desc) in SCHEMA.items():
        print(f"{name:<10}{len(tables[name]):>7}  {pk:<12}{desc}")

    print("\n外键关系（Power BI 里的一条连线 = 一个外键）：")
    print("  disp.client_id   → clients.client_id")
    print("  disp.account_id  → accounts.account_id")
    print("  card.disp_id     → disp.disp_id")
    print("  loans.account_id → accounts.account_id")
    print("  order.account_id → accounts.account_id")
    print("  trans.account_id → accounts.account_id")
    print("  clients.district_id / accounts.district_id → district.district_id")


def build_star(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """还原教材的维度模型：事实表 trans ← 账户 ← 客户 ← 地区。"""
    trans = tables["trans"]
    accounts = tables["accounts"][["account_id", "district_id", "frequency", "date"]] \
        .rename(columns={"district_id": "account_district", "date": "account_date",
                         "frequency": "statement_freq"})
    # disp 是「客户-账户」多对多桥表：一个账户可能有多个持有人
    disp = tables["disp"][["disp_id", "client_id", "account_id", "type"]] \
        .rename(columns={"type": "disp_type"})
    clients = tables["clients"][["client_id", "sex", "birth_date", "district_id"]] \
        .rename(columns={"district_id": "client_district"})
    district = tables["district"].rename(columns={"district_id": "client_district"})

    star = (trans
            .merge(accounts, on="account_id", how="left")
            .merge(disp, on="account_id", how="left")
            .merge(clients, on="client_id", how="left")
            .merge(district, on="client_district", how="left"))
    # 派生维度：年龄（以事实表的交易年份为准，避免"现在"带来的偏差）
    star["trans_date"] = pd.to_datetime(star["date"], errors="coerce")
    star["birth"] = pd.to_datetime(star["birth_date"], errors="coerce")
    star["age"] = (star["trans_date"] - star["birth"]).dt.days / 365.25
    star["age_band"] = pd.cut(star["age"], [0, 25, 35, 45, 55, 65, 120],
                              labels=["<25", "25-35", "35-45", "45-55", "55-65", "65+"])
    star["year"] = star["trans_date"].dt.year
    return star


def analyse(star: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """教材里用 Power BI 拖字段做的四张透视表，这里用 groupby 复现。"""
    results = {}

    # 1) 按地区：交易额、交易笔数、人均交易额（地区维表带人口）
    by_district = (star.dropna(subset=["client_district"])
                   .groupby("client_district")
                   .agg(tx_cnt=("trans_id", "count"),
                        amount=("amount", "sum"),
                        population=("population", "max"))
                   .reset_index()
                   .rename(columns={"client_district": "district_id"}))
    by_district["amount_per_capita"] = by_district["amount"] / by_district["population"]
    results["by_district"] = by_district.sort_values("amount", ascending=False)

    # 2) 按性别 × 年龄组：交易额（对比分析 / 构成分析）
    by_seg = (star.dropna(subset=["sex", "age_band"])
              .groupby(["sex", "age_band"], observed=True)
              .agg(tx_cnt=("trans_id", "count"), amount=("amount", "sum"),
                   avg_amount=("amount", "mean"))
              .reset_index())
    results["by_segment"] = by_seg

    # 3) 按对账单频率：账户活跃度
    by_freq = (star.groupby("statement_freq")
               .agg(accounts=("account_id", "nunique"), tx_cnt=("trans_id", "count"),
                    amount=("amount", "sum"))
               .reset_index())
    results["by_frequency"] = by_freq.sort_values("amount", ascending=False)

    # 4) 按贷款状态：贷款金额与笔数（另一条支路：loans ⋈ accounts）
    loans = pd.read_csv(os.path.join(DATA, "loans.csv"))
    by_loan = (loans.groupby("status")
               .agg(loans=("loan_id", "count"), amount=("amount", "sum"),
                    avg_amount=("amount", "mean"))
               .reset_index())
    results["by_loan_status"] = by_loan.sort_values("amount", ascending=False)
    return results


def plot(results: dict[str, pd.DataFrame]) -> None:
    d = results["by_district"].head(12)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=150)
    axes[0].barh(d["district_id"].astype(str)[::-1], d["amount"][::-1] / 1e6,
                 color="#4472C4")
    axes[0].set_title("交易额前 12 的地区（百万）", fontsize=11)
    axes[0].set_xlabel("交易额（百万）")
    axes[0].grid(axis="x", color="#E1E4E8")
    axes[0].set_axisbelow(True)

    seg = results["by_segment"].pivot(index="age_band", columns="sex", values="amount")
    seg.plot(kind="bar", ax=axes[1], color=["#ED7D31", "#4472C4", "#70AD47"][:seg.shape[1]])
    axes[1].set_title("各年龄段交易额（按性别）", fontsize=11)
    axes[1].set_xlabel("年龄段")
    axes[1].set_ylabel("交易额")
    axes[1].tick_params(axis="x", rotation=0)
    axes[1].grid(axis="y", color="#E1E4E8")
    axes[1].set_axisbelow(True)
    plt.tight_layout()
    path = os.path.join(OUT, "ch01_schema.png")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\n图已保存：{os.path.relpath(path, ROOT)}")


def main() -> int:
    tables = load()
    show_schema(tables)
    star = build_star(tables)
    print(f"\n星型模型展开后：{len(star):,} 行 × {star.shape[1]} 列"
          f"（事实表 trans {len(tables['trans']):,} 行左连接维表）")

    results = analyse(star)
    print("\n" + "=" * 78)
    print("二、在星型模型上做分析（教材 Power BI 透视表的等价物）")
    print("=" * 78)
    for name, df in results.items():
        path = os.path.join(OUT, f"ch01_{name}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"\n[{name}] → outputs/ch01_{name}.csv")
        print(df.head(6).to_string(index=False))

    plot(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
