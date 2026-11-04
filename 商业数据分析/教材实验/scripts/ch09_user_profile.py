"""第 9 章 用户标签体系与用户画像 · 信用卡客户画像

教材原做法
----------
第 9 章配套 `信用卡客户画像.sql`：以「发卡时点」为观测点，用三表连接
（kdd99_card ⋈ kdd99_disp ⋈ kdd99_clients / kdd99_trans）取两批特征：

1. 客户属性：性别、发卡时年龄 = datediff(issued, birth_date)/365
2. 行为特征：截止发卡时的「最后一次交易间隔」与「账户余额」→ 也就是发卡时点的 R 和 M

教材的关键方法论是**时点数据（point-in-time）**：所有特征都只能用「发卡之前」的数据，
否则会把未来的信息泄漏进画像（数据泄漏，leakage）。

迁移思路
--------
1. 用 pandas 的 merge + 条件过滤复现这个「as-of 连接」（等价于 SQL 的
   `on a.issued > c.date`，也叫 temporal join）；
2. 把连续特征分箱成标签（等频/等距），拼成「用户标签宽表」；
3. 出画像：性别 × 年龄、余额分层、活跃度分层、标签组合 Top。

运行：python scripts/ch09_user_profile.py
输出：outputs/ch09_*.csv、outputs/ch09_profile.png
"""
from __future__ import annotations

import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch01")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
C_MAIN, C_ALT, C_GREEN, C_GRAY = "#4472C4", "#ED7D31", "#70AD47", "#A5A5A5"
GRID = "#E1E4E8"


def num(s: pd.Series) -> pd.Series:
    """去掉千分位再转数值（原表金额是 "1,200" 这种字符串）。"""
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False).str.strip(),
                         errors="coerce")


def load() -> dict[str, pd.DataFrame]:
    t = {}
    for name in ("card", "disp", "clients", "trans", "accounts"):
        df = pd.read_csv(os.path.join(DATA, f"{name}.csv"))
        for col in ("amount", "balance"):
            if col in df.columns:
                df[col] = num(df[col])
        t[name] = df
    return t


def as_of_feature(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """发卡时点画像：card ⋈ disp ⋈ clients，再 as-of 连接发卡前的交易。

    这对应教材 SQL 里的：
        left join kdd99_trans c
               on b.account_id = c.account_id and a.issued > c.date
    pandas 里没有 as-of 语法糖，用 merge + 布尔过滤 + groupby(last) 实现。
    """
    card = t["card"].copy()
    card["issued"] = pd.to_datetime(card["issued"], errors="coerce")
    disp = t["disp"][["disp_id", "client_id", "account_id"]]
    clients = t["clients"][["client_id", "sex", "birth_date"]]
    clients["birth_date"] = pd.to_datetime(clients["birth_date"], errors="coerce")
    trans = t["trans"][["account_id", "date", "amount", "balance", "type"]].copy()
    trans["date"] = pd.to_datetime(trans["date"], errors="coerce")

    base = (card.merge(disp, on="disp_id", how="left")
                .merge(clients, on="client_id", how="left"))
    base["age_at_issue"] = ((base["issued"] - base["birth_date"]).dt.days / 365.25).round(1)

    # as-of 连接：只保留 issued > date 的流水（发卡之前的），每张卡取最后一笔
    joined = base[["card_id", "account_id", "issued"]].merge(
        trans, on="account_id", how="left")
    before = joined[joined["date"] < joined["issued"]]
    last = (before.sort_values("date")
            .groupby("card_id")
            .agg(last_trans_date=("date", "max"),
                 last_balance=("balance", "last"),
                 trans_cnt_before=("date", "size"),
                 amount_sum_before=("amount", "sum"))
            .reset_index())

    feat = base.merge(last, on="card_id", how="left")
    feat["idle_days"] = (feat["issued"] - feat["last_trans_date"]).dt.days
    return feat


def tag(feat: pd.DataFrame) -> pd.DataFrame:
    """连续特征 → 标签：等距分箱用于年龄/余额，等频用于活跃度。"""
    f = feat.dropna(subset=["age_at_issue"]).copy()

    f["年龄段"] = pd.cut(f["age_at_issue"], [0, 30, 40, 50, 60, 200],
                       labels=["≤30岁", "31-40岁", "41-50岁", "51-60岁", ">60岁"])
    f["性别"] = f["sex"].where(f["sex"].isin(["男", "女"]), "未知")

    # 余额分层：按分位数切（信用卡余额右偏，等距切会全挤在最低档）
    f["余额分层"] = pd.qcut(f["last_balance"], 4,
                          labels=["低余额", "中低余额", "中高余额", "高余额"],
                          duplicates="drop")
    # 活跃度：这里用「发卡前交易笔数」分四档。
    # 注：教材原意是用「距最后一次交易的天数」度量活跃，但 KDD99 的发卡日几乎都紧贴
    # 该账户的第一笔交易（idle_days 全在 1—27 天之间），按天数切箱会得到单一档位，
    # 没有区分度，所以换成交易笔数——这也是迁移时该做的判断：先看分布再定分箱。
    f["活跃度"] = pd.qcut(f["trans_cnt_before"].fillna(0).rank(method="first"), 4,
                       labels=["低活跃", "中低活跃", "中高活跃", "高活跃"])
    f["卡类型"] = f["type"].fillna("未知")

    # 组合标签：教材强调「标签不是单列，而是可组合的画像」
    f["画像标签"] = (f["性别"].astype(str) + "·" + f["年龄段"].astype(str)
                  + "·" + f["余额分层"].astype(str))
    return f


def report(f: pd.DataFrame) -> None:
    print(f"\n画像样本：{len(f):,} 张卡（发卡时点有出生日期的）")
    print(f"  平均发卡年龄 {f['age_at_issue'].mean():.1f} 岁，"
          f"中位余额 {f['last_balance'].median():,.0f}，"
          f"特征缺失率 {f['idle_days'].isna().mean():.2%}")

    for col in ("性别", "年龄段", "余额分层", "活跃度", "卡类型"):
        s = f[col].value_counts(dropna=False)
        print(f"\n[{col}]")
        print((s / len(f) * 100).round(2).rename("占比%").to_frame()
              .assign(人数=s).to_string())

    combo = (f["画像标签"].value_counts().head(10).rename("人数").to_frame()
             .assign(占比=lambda d: (d["人数"] / len(f) * 100).round(2)))
    print("\n[标签组合 Top10]")
    print(combo.to_string())
    combo.reset_index(names="画像标签").to_csv(
        os.path.join(OUT, "ch09_combo.csv"), index=False, encoding="utf-8-sig")


def plot(f: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), dpi=150)

    a = axes[0][0]
    tab = pd.crosstab(f["年龄段"], f["性别"], normalize="index") * 100
    tab.plot(kind="bar", ax=a, color=[C_ALT, C_MAIN], width=0.72)
    a.set_title("各年龄段的性别构成（%）", fontsize=10.5)
    a.set_xlabel("")
    a.tick_params(axis="x", rotation=0)
    a.legend(title="", fontsize=8.5)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    a = axes[0][1]
    bal = f["余额分层"].value_counts().reindex(["低余额", "中低余额", "中高余额", "高余额"])
    a.bar(bal.index, bal.values / len(f) * 100, color=C_GREEN)
    for i, v in enumerate(bal.values / len(f) * 100):
        a.text(i, v, f"{v:.1f}%", ha="center", va="bottom", fontsize=8.5)
    a.set_title("余额分层占比", fontsize=10.5)
    a.set_ylabel("%")
    a.tick_params(axis="x", rotation=10)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    a = axes[1][0]
    act = f["活跃度"].value_counts().reindex(
        ["低活跃", "中低活跃", "中高活跃", "高活跃"])
    a.barh(act.index[::-1], act.values[::-1] / len(f) * 100, color=C_MAIN)
    a.set_title("发卡前交易笔数分层（活跃度）", fontsize=10.5)
    a.set_xlabel("%")
    a.grid(axis="x", color=GRID)
    a.set_axisbelow(True)

    a = axes[1][1]
    a.hist(f["age_at_issue"].dropna(), bins=20, color=C_GRAY, edgecolor="white")
    a.axvline(f["age_at_issue"].mean(), color=C_ALT, ls="--", lw=1.4,
              label=f"均值 {f['age_at_issue'].mean():.1f} 岁")
    a.set_title("发卡年龄分布", fontsize=10.5)
    a.set_xlabel("年龄")
    a.set_ylabel("卡数")
    a.legend(fontsize=8.5)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(OUT, "ch09_profile.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\n图 → {os.path.relpath(path, ROOT)}")


def main() -> int:
    print("=" * 78)
    print("第 9 章 · 用户标签体系与用户画像（信用卡客户画像）")
    print("=" * 78)
    t = load()
    feat = as_of_feature(t)
    print(f"\n发卡记录 {len(feat):,} 张，as-of 融合后特征列 "
          f"{len(feat.columns)} 个：{', '.join(feat.columns[:8])} …")

    f = tag(feat)
    report(f)
    plot(f)

    keep = ["card_id", "account_id", "issued", "性别", "年龄段", "age_at_issue",
            "余额分层", "last_balance", "活跃度", "idle_days", "卡类型",
            "trans_cnt_before", "amount_sum_before", "画像标签"]
    out = f[keep].copy()
    out.to_csv(os.path.join(OUT, "ch09_user_profile.csv"), index=False,
               encoding="utf-8-sig")
    print(f"  → {os.path.relpath(os.path.join(OUT, 'ch09_user_profile.csv'), ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
