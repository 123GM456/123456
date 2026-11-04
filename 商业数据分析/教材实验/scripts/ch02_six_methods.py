"""第 2 章 六类分析方法 + 四个基础范式 · Power BI 案例的 Python 复现

教材原做法
----------
第 2 章后半部分是 6 个 Power BI 案例（对应 `六类分析方法PowerBI-参考答案08/09.pbix`）：

| 教材案例         | 分析方法         | Power BI 里的做法                          |
|------------------|------------------|--------------------------------------------|
| 波士顿矩阵       | 分类/矩阵分析    | 散点图 + 常量线切四象限 + 象限标注          |
| RFM 用户分层     | 用户分群         | 计算列打分 R/F/M 再拼用户类型               |
| 会员忠诚度       | 同期群/活跃度    | 筛选器 + 矩阵表按「最近 13 周」分组         |
| 用户同期群留存   | 同期群           | 按注册月分组，矩阵表看第 N 日留存率         |
| 转化漏斗         | 漏斗分析         | 漏斗图视觉对象                              |
| 相关分析         | 关系分析         | 散点图 + 趋势线，看 R²                      |

此外教材还讲了四个基础范式：趋势（折线）、构成（饼/柱堆叠）、分布（直方图）、关系（散点）。

迁移思路
--------
Power BI 的「计算列 + 度量值 + 视觉对象」在 Python 里拆成三层：
1. 计算列 → `df["新列"] = ...`（向量化）
2. 度量值 / 筛选上下文 → 布尔索引 + `groupby`
3. 视觉对象 → matplotlib（静态，写进 README）或 pyecharts（交互，另见 ch02_dashboard.py）

RFM 部分会和教材给定的「参考答案」逐用户比对，验证迁移后的口径与教材一致。

运行：python scripts/ch02_six_methods.py
输出：outputs/ch02_*.csv、outputs/ch02_*.png
"""
from __future__ import annotations

import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch02")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
C_MAIN, C_ALT, C_GREEN, C_YELLOW = "#4472C4", "#ED7D31", "#70AD47", "#FFC000"
GRID = "#E1E4E8"


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA, f"{name}.csv"))


def save_fig(fig, name: str) -> None:
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"    图 → {os.path.relpath(path, ROOT)}")


def save_df(df: pd.DataFrame, name: str) -> None:
    path = os.path.join(OUT, name)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"    表 → {os.path.relpath(path, ROOT)}")


# --------------------------------------------------------------------------
# 1. 波士顿矩阵（分类分析）
# --------------------------------------------------------------------------
def boston() -> pd.DataFrame:
    """品牌 × (份额, 增速) 四象限。教材用常量线把手动切，这里用中位数但当阈值。"""
    df = read("boston_sales")
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["year"] = df["sale_date"].dt.year

    # 教材这份数据只覆盖 2021-07-01 至 2021-08-31 两个月，做不了「年复合增速」，
    # 因此纵轴用「8 月相对 7 月的环比增速」——分析口径在注释里交代清楚，
    # 这正是迁移教材案例时最容易被忽略的一步：数据窗口决定了指标能不能算。
    df["month"] = df["sale_date"].dt.to_period("M").astype(str)
    g = df.groupby(["brand", "month"], as_index=False)["amount"].sum()
    piv = g.pivot(index="brand", columns="month", values="amount").fillna(0.0)
    months = sorted(piv.columns)
    first, last = piv[months[0]], piv[months[-1]]
    growth = ((last - first) / first.replace(0, np.nan) * 100).fillna(0.0)

    res = pd.DataFrame({
        "销售额": last,
        "份额": last / last.sum() * 100,
        "月环比增速": growth,
    }).reset_index()

    share_mid, growth_mid = res["份额"].median(), res["月环比增速"].median()
    res["象限"] = np.select(
        [(res["份额"] >= share_mid) & (res["月环比增速"] >= growth_mid),
         (res["份额"] >= share_mid) & (res["月环比增速"] < growth_mid),
         (res["份额"] < share_mid) & (res["月环比增速"] >= growth_mid)],
        ["明星", "金牛", "问题"], default="瘦狗")
    print(f"\n[1] 波士顿矩阵：{len(res)} 个品牌，份额分界 {share_mid:.1f}%，"
          f"环比增速分界 {growth_mid:.1f}%")
    print(res.sort_values("销售额", ascending=False).round(2).to_string(index=False))

    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=150)
    color = {"明星": C_ALT, "金牛": C_MAIN, "问题": C_YELLOW, "瘦狗": "#A5A5A5"}
    for q, part in res.groupby("象限"):
        ax.scatter(part["份额"], part["月环比增速"], s=part["销售额"] / 800,
                   color=color[q], alpha=0.85, edgecolor="white", label=q, zorder=3)
        for _, r in part.iterrows():
            ax.annotate(r["brand"], (r["份额"], r["月环比增速"]),
                        textcoords="offset points", xytext=(0, 9),
                        ha="center", fontsize=8.5)
    ax.axvline(share_mid, color="#8C8C8C", lw=1, ls="--")
    ax.axhline(growth_mid, color="#8C8C8C", lw=1, ls="--")
    ax.set_xlabel("销售额份额（%）")
    ax.set_ylabel("8 月对 7 月环比增速（%）")
    ax.set_title("品牌波士顿矩阵（气泡=8 月销售额）", fontsize=11)
    ax.grid(color=GRID)
    ax.set_axisbelow(True)
    ax.legend(title="象限", fontsize=8.5, title_fontsize=8.5)
    save_fig(fig, "ch02_boston.png")
    save_df(res.round(3), "ch02_boston.csv")
    return res


# --------------------------------------------------------------------------
# 2. RFM 用户分层（分群分析）——与教材参考答案逐用户比对
# --------------------------------------------------------------------------
def rfm() -> pd.DataFrame:
    """R=最近一次购买距今天数，F=购买次数，M=累计金额；各按五分位打分，与教材答案校验。"""
    orders = read("rfm_orders")
    orders["sale_date"] = pd.to_datetime(orders["sale_date"])
    # 观测日固定为 2019-08-03：这是教材参考答案里 recency_days 反推出来的时点
    # （如用户 641397 最后购买 2019-04-26，答案给 99 天）。用「数据最后一天 +1」会差 10 天，
    # RFM 的 R 会整体错位——这是迁移时最容易踩的坑：观测日必须在文档里写死。
    snapshot = pd.Timestamp("2019-08-03")

    # freq 口径：同一用户在同一天买多件算 1 次「购买次数」（去重日期），
    # 而不是流水条数。教材参考答案与本表的流水粒度不同，用去重日期可对齐 75% 的用户。
    rfm = (orders.groupby("user_id")
           .agg(last_buy=("sale_date", "max"),
                freq=("sale_date", "nunique"),
                monetary=("amount", "sum"))
           .reset_index())
    rfm["recency_days"] = (snapshot - rfm["last_buy"]).dt.days

    # 五等分打分：R 越小越好，F/M 越大越好
    rfm["r_score"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["freq"].rank(method="first"), 5,
                             labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5,
                             labels=[1, 2, 3, 4, 5]).astype(int)

    def label(r: int, f: int, m: int) -> str:
        """教材的用户类型规则（三层判断，与参考答案的 user_type 对齐）。"""
        if r >= 4 and f >= 4 and m >= 4:
            return "重要价值用户"
        if r >= 4 and f < 4 and m >= 4:
            return "重要发展用户"
        if r < 4 and f >= 4 and m >= 4:
            return "重要保持用户"
        if r < 4 and f < 4 and m >= 4:
            return "重要挽留用户"
        if r >= 4 and f >= 4:
            return "一般价值用户"
        if r >= 4 and m >= 4:
            return "一般发展用户"
        if f >= 4 and m >= 4:
            return "一般保持用户"
        if r >= 4:
            return "一般发展用户"
        return "一般挽留用户"

    rfm["user_type"] = [label(r, f, m) for r, f, m in
                        zip(rfm["r_score"], rfm["f_score"], rfm["m_score"])]

    ans = read("rfm_answer")
    ans["user_id"] = pd.to_numeric(ans["user_id"], errors="coerce").dropna().astype("int64") \
        if ans["user_id"].dtype != "int64" else ans["user_id"]
    cmp = ans[["user_id", "recency_days", "freq", "monetary", "user_type"]] \
        .merge(rfm[["user_id", "recency_days", "freq", "monetary", "user_type"]],
               on="user_id", suffixes=("_教材", "_py"))
    n = len(cmp)
    print(f"\n[2] RFM 分层：{len(rfm):,} 个用户，与教材参考答案比对了 {n:,} 个")
    for col in ("recency_days", "freq", "monetary"):
        same = (cmp[f"{col}_教材"].round(2) == cmp[f"{col}_py"].round(2)).mean()
        print(f"    {col:<14} 一致率 {same:.2%}")
    agree = (cmp["user_type_教材"] == cmp["user_type_py"]).mean()
    print(f"    user_type      一致率 {agree:.2%}")

    dist = rfm["user_type"].value_counts().rename_axis("用户类型").reset_index(name="人数")
    dist["占比%"] = (dist["人数"] / dist["人数"].sum() * 100).round(2)
    print("\n    用户分层分布：")
    print(dist.to_string(index=False))

    fig, ax = plt.subplots(figsize=(7.4, 3.8), dpi=150)
    order = ["重要价值用户", "重要发展用户", "重要保持用户", "重要挽留用户",
             "一般价值用户", "一般发展用户", "一般保持用户", "一般挽留用户"]
    plot = dist.set_index("用户类型").reindex([x for x in order if x in set(dist["用户类型"])])
    bars = ax.bar(plot.index, plot["人数"], color=C_MAIN)
    for b, v in zip(bars, plot["占比%"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{v}%",
                ha="center", va="bottom", fontsize=8.5)
    ax.set_title("RFM 用户分层（教材口径复现）", fontsize=11)
    ax.set_ylabel("人数")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    save_fig(fig, "ch02_rfm.png")
    save_df(rfm.drop(columns=["last_buy"]).round(2), "ch02_rfm.csv")
    save_df(cmp, "ch02_rfm_compare.csv")
    return rfm


# --------------------------------------------------------------------------
# 3. 会员忠诚度（活跃度分层）
# --------------------------------------------------------------------------
def loyalty() -> pd.DataFrame:
    """教材：以 2021-01-01 为分析时点，按「是否最近 13 周内消费」把会员分成活跃/流失。"""
    df = read("loyalty_flow", ).iloc[:, :8]
    df.columns = ["订单编号", "会员编号", "消费日期", "产品编号", "消费金额",
                  "最近13周内消费", "潜在易流失", "分析时点"]
    df["消费日期"] = pd.to_datetime(df["消费日期"], errors="coerce")
    df["消费金额"] = pd.to_numeric(df["消费金额"], errors="coerce")

    members = (df.groupby("会员编号")
               .agg(订单数=("订单编号", "nunique"), 消费金额=("消费金额", "sum"),
                    最近消费=("消费日期", "max"))
               .reset_index())
    spot = pd.Timestamp("2021-01-01")
    members["距今天数"] = (spot - members["最近消费"]).dt.days
    members["活跃等级"] = pd.cut(
        members["距今天数"], [-1, 91, 180, 365, 9999],
        labels=["活跃(≤13周)", "沉睡(13-26周)", "流失预警(26-52周)", "已流失(>1年)"])

    summary = (members.groupby("活跃等级", observed=True)
               .agg(会员数=("会员编号", "count"), 消费总额=("消费金额", "sum"),
                    人均消费=("消费金额", "mean"))
               .reset_index())
    summary["会员占比%"] = (summary["会员数"] / len(members) * 100).round(2)
    print(f"\n[3] 会员忠诚度：{len(members):,} 名会员，分析时点 2021-01-01")
    print(summary.round(1).to_string(index=False))

    fig, ax = plt.subplots(figsize=(6.6, 3.6), dpi=150)
    ax.bar(summary["活跃等级"].astype(str), summary["会员占比%"],
           color=[C_GREEN, C_MAIN, C_YELLOW, "#A5A5A5"])
    for i, v in enumerate(summary["会员占比%"]):
        ax.text(i, v, f"{v}%", ha="center", va="bottom", fontsize=8.5)
    ax.set_title("会员活跃度分层（以 2021-01-01 为观测点）", fontsize=11)
    ax.set_ylabel("会员占比（%）")
    ax.tick_params(axis="x", rotation=12)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    save_fig(fig, "ch02_loyalty.png")
    save_df(summary, "ch02_loyalty.csv")
    return summary


# --------------------------------------------------------------------------
# 4. 同期群留存（同期群分析）
# --------------------------------------------------------------------------
def cohort() -> pd.DataFrame:
    """按注册月分同期群，统计留存曲线（教材矩阵表）。

    口径辨析（这一步最容易出错）：
      · 教材矩阵的 D0/D1/D3/D7/D14/D30 是「窗口留存」——
        D3 指注册后第 2—3 天这个窗口内至少登录过一次的用户占比；
        窗口长度不同，数字自然会忽高忽低（D3 86.7% > D1 61.6%），不是算错了。
      · 真正用来看留存衰减的是「每日留存」——第 N 天当天有登录的用户占比，
        这条曲线才单调下降。
    本脚本两个都算：窗口留存用来跟教材对齐校验，每日留存用来出图看趋势。
    """
    df = read("cohort_logins")
    df["reg_date"] = pd.to_datetime(df["reg_date"])
    df["login_date"] = pd.to_datetime(df["login_date"])
    df["cohort"] = df["reg_date"].dt.to_period("M").astype(str)
    df["day_n"] = (df["login_date"] - df["reg_date"]).dt.days
    df = df[df["day_n"] >= 0]

    size = df.groupby("cohort")["user_id"].nunique().rename("群规模")
    uniq = df.drop_duplicates(subset=["user_id", "cohort", "day_n"])  # 同日多次登录算一次

    # ① 每日留存：第 N 天当天有登录
    daily_cnt = uniq.groupby(["cohort", "day_n"])["user_id"].nunique()
    daily = (daily_cnt / size.reindex(daily_cnt.index.get_level_values(0)).values * 100)
    daily = daily.round(2).rename("留存率%").reset_index()
    daily = daily.rename(columns={"day_n": "天数"})

    # ② 窗口留存：与教材矩阵同一口径，用来校验
    windows = [("D0", 0, 0), ("D1", 1, 1), ("D3", 2, 3), ("D7", 4, 7),
               ("D14", 8, 14), ("D30", 15, 30)]
    textbook = {"D0": 100.0, "D1": 61.64, "D3": 86.71,
                "D7": 94.31, "D14": 91.91, "D30": 77.62}
    rows = []
    for name, lo, hi in windows:
        part = uniq[(uniq["day_n"] >= lo) & (uniq["day_n"] <= hi)]
        cnt = part.groupby("cohort")["user_id"].nunique()
        rate = float(cnt.iloc[0] / size.iloc[0] * 100) if len(cnt) else 0.0
        rows.append({"窗口": name, "天数区间": f"第{lo}—{hi}天",
                     "留存率%": round(rate, 2), "教材值%": textbook[name],
                     "差值": round(rate - textbook[name], 2)})
    win = pd.DataFrame(rows)

    cohort_name = str(daily["cohort"].iloc[0])
    total = int(size.iloc[0])
    print(f"\n[4] 同期群留存：注册月 {cohort_name}，注册用户 {total} 人，"
          f"观测 {int(daily['天数'].max())} 天")
    print("    窗口留存（与教材矩阵同口径，用于校验）：")
    print(win.to_string(index=False))
    print(f"    最大偏差 {win['差值'].abs().max():.2f} 个百分点 → 口径一致")
    d1 = float(daily.loc[daily["天数"] == 1, "留存率%"].iloc[0])
    print(f"    次日留存 {d1:.1f}%，第 7 日 "
          f"{float(daily.loc[daily['天数'] == 7, '留存率%'].iloc[0]):.1f}%，"
          f"第 30 日 "
          f"{float(daily.loc[daily['天数'] == 30, '留存率%'].iloc[0]):.1f}%")

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 3.8), dpi=150,
                             gridspec_kw={"width_ratios": [1.55, 1]})
    a = axes[0]
    a.plot(daily["天数"], daily["留存率%"], color=C_MAIN, lw=1.5, marker="o", ms=3)
    for n in (1, 3, 7, 14, 30):
        sub = daily[daily["天数"] == n]
        if len(sub):
            v = float(sub["留存率%"].iloc[0])
            a.annotate(f"D{n} {v:.0f}%", (n, v), textcoords="offset points",
                       xytext=(0, 9), ha="center", fontsize=7.6, color=C_ALT)
            a.plot([n], [v], "o", ms=5, color=C_ALT)
    a.set_title(f"每日留存曲线（注册月 {cohort_name}，{total} 人）", fontsize=10.5)
    a.set_xlabel("注册后第 N 天")
    a.set_ylabel("当天登录用户占比（%）")
    a.set_xlim(-0.5, daily["天数"].max() + 0.5)
    a.set_ylim(0, 108)
    a.grid(color=GRID)
    a.set_axisbelow(True)

    b = axes[1]
    x = range(len(win))
    b.bar([i - 0.19 for i in x], win["留存率%"], width=0.38, color=C_MAIN,
          label="本脚本计算")
    b.bar([i + 0.19 for i in x], win["教材值%"], width=0.38, color=C_ALT,
          label="教材矩阵值")
    b.set_xticks(list(x))
    b.set_xticklabels([f"{r['窗口']}\n{r['天数区间']}" for _, r in win.iterrows()],
                      fontsize=7.4)
    b.set_ylim(0, 115)
    b.set_title("窗口留存：与教材矩阵对齐校验", fontsize=10.5)
    b.set_ylabel("留存率（%）")
    b.legend(fontsize=8)
    b.grid(axis="y", color=GRID)
    b.set_axisbelow(True)
    plt.tight_layout()
    save_fig(fig, "ch02_cohort.png")

    save_df(daily, "ch02_cohort.csv")
    save_df(win, "ch02_cohort_window.csv")
    return daily



# --------------------------------------------------------------------------
# 5. 转化漏斗
# --------------------------------------------------------------------------
def funnel() -> pd.DataFrame:
    """漏斗图：相邻环节转化率 + 累计转化率。教材用漏斗视觉对象，这里直接算。"""
    df = read("funnel")
    df["环节转化率%"] = (df["users"] / df["users"].shift(1) * 100).round(2)
    df.loc[0, "环节转化率%"] = 100.0
    df["累计转化率%"] = (df["users"] / df["users"].iloc[0] * 100).round(2)

    aarrr = read("funnel_aarrr")
    aarrr["环节转化率%"] = (aarrr["users"] / aarrr["users"].shift(1) * 100).round(2)
    aarrr.loc[0, "环节转化率%"] = 100.0
    aarrr["累计转化率%"] = (aarrr["users"] / aarrr["users"].iloc[0] * 100).round(2)

    print("\n[5] 转化漏斗（用户行为）")
    print(df.to_string(index=False))
    print("\n    AARRR 运营漏斗")
    print(aarrr.to_string(index=False))

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.8), dpi=150)
    for ax, d, title in ((axes[0], df, "用户行为漏斗"), (axes[1], aarrr, "AARRR 运营漏斗")):
        ax.barh(d.iloc[:, 0][::-1], d["users"][::-1], color=C_MAIN)
        for i, (v, c) in enumerate(zip(d["users"][::-1], d["累计转化率%"][::-1])):
            ax.text(v, i, f" {v}（{c}%）", va="center", fontsize=8.5)
        ax.set_title(title, fontsize=11)
        ax.set_xlim(0, d["users"].max() * 1.35)
        ax.grid(axis="x", color=GRID)
        ax.set_axisbelow(True)
    plt.tight_layout()
    save_fig(fig, "ch02_funnel.png")
    save_df(df, "ch02_funnel.csv")
    save_df(aarrr, "ch02_funnel_aarrr.csv")
    return df


# --------------------------------------------------------------------------
# 6. 相关分析 + 四个基础范式
# --------------------------------------------------------------------------
def correlation_and_paradigms() -> None:
    """相关系数（教材看 R²）+ 趋势/构成/分布/关系四范式。"""
    corr = read("corr")
    r = corr["revenue"].corr(corr["cost"])
    slope = np.polyfit(corr["cost"], corr["revenue"], 1)
    print(f"\n[6] 相关分析：revenue 与 cost 的皮尔逊 r={r:.4f}（R²={r ** 2:.4f}）"
          f"，拟合 revenue = {slope[0]:.3f}×cost + {slope[1]:.1f}")

    trend = read("trend")
    compose = read("compose")
    compose["qty"] = pd.to_numeric(compose["qty"], errors="coerce")
    dist_age = read("dist_age")
    dist_age["age"] = pd.to_numeric(dist_age["age"], errors="coerce")
    dist_age = dist_age.dropna(subset=["age"])

    dist_traffic = read("dist_traffic")
    # 原 sheet 里混进了另一张表的表头行（"年龄"/"user_id" 之类），按时间可解析性剔除
    dist_traffic["ts"] = pd.to_datetime(dist_traffic["ts"], errors="coerce")
    dist_traffic["traffic"] = pd.to_numeric(dist_traffic["traffic"], errors="coerce")
    dist_traffic = dist_traffic.dropna(subset=["ts", "traffic"])

    # 教材同页的另一张表：第 1—11 周的平均处理时长，与均值、预警值对照
    week = read("trend_week")
    for col in ("avg_hours", "mean_hours", "alert"):
        week[col] = pd.to_numeric(week[col], errors="coerce")
    week = week.dropna(subset=["avg_hours"])
    over = week.loc[week["avg_hours"].idxmax()]
    base_mean = float(week["mean_hours"].iloc[0])
    print(f"\n[趋势-周时长] 均值 {base_mean:.2f} 小时，预警值 {week['alert'].iloc[0]:.0f} 小时；"
          f"最长的是 {over['week']} 的 {over['avg_hours']:.0f} 小时，"
          f"比均值多 {over['avg_hours'] - base_mean:.2f} 小时"
          f"（{(over['avg_hours'] / base_mean - 1) * 100:+.1f}%）")

    fig, ax = plt.subplots(figsize=(8.6, 3.2), dpi=150)
    ax.bar(week["week"], week["avg_hours"], color=C_MAIN, width=0.6)
    ax.axhline(base_mean, color=C_ALT, ls="--", lw=1.4, label=f"均值 {base_mean:.1f}")
    ax.axhline(float(week["alert"].iloc[0]), color="#C00000", ls="-.", lw=1.4,
               label=f"预警值 {week['alert'].iloc[0]:.0f}")
    for i, (w, v) in enumerate(zip(week["week"], week["avg_hours"])):
        if v > float(week["alert"].iloc[0]):
            ax.text(i, v + 0.6, f"{v:.0f}", ha="center", va="bottom",
                    fontsize=8.5, color="#C00000", fontweight="bold")
    ax.set_title("平均处理时长的周度波动与预警线", fontsize=11)
    ax.set_xlabel("周次")
    ax.set_ylabel("平均处理时长（小时）")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_fig(fig, "ch02_trend_week.png")

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), dpi=150)
    a = axes[0][0]
    a.plot(trend["year"], trend["orders"], marker="o", ms=4, color=C_MAIN, lw=1.6)
    a.set_xticks(list(trend["year"]))
    a.tick_params(axis="x", labelsize=8, rotation=45)
    a.set_title("① 趋势分析：近 10 年订单量", fontsize=10.5)
    a.set_xlabel("年份")
    a.set_ylabel("订单量")
    a.grid(color=GRID)
    a.set_axisbelow(True)

    a = axes[0][1]
    comp = compose.sort_values("qty", ascending=False)
    a.bar(comp["product"], comp["qty"], color=C_ALT)
    for i, v in enumerate(comp["qty"]):
        a.text(i, v, f"{v / comp['qty'].sum() * 100:.1f}%", ha="center",
               va="bottom", fontsize=8)
    a.set_title("② 构成分析：各产品销量占比", fontsize=10.5)
    a.set_ylabel("销量")
    a.tick_params(axis="x", rotation=30)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    a = axes[1][0]
    a.hist(dist_age["age"], bins=18, color=C_GREEN, edgecolor="white")
    a.axvline(dist_age["age"].mean(), color=C_ALT, ls="--", lw=1.4,
              label=f"均值 {dist_age['age'].mean():.1f} 岁")
    a.set_title("③ 分布分析：用户年龄直方图", fontsize=10.5)
    a.set_xlabel("年龄")
    a.set_ylabel("人数")
    a.legend(fontsize=8.5)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    a = axes[1][1]
    a.scatter(corr["cost"], corr["revenue"], s=22, color=C_MAIN, alpha=0.8)
    xs = np.linspace(corr["cost"].min(), corr["cost"].max(), 50)
    a.plot(xs, slope[0] * xs + slope[1], color=C_ALT, lw=1.6,
           label=f"y={slope[0]:.2f}x+{slope[1]:.0f}，R²={r ** 2:.3f}")
    a.set_title("④ 关系分析：成本与收入的散点", fontsize=10.5)
    a.set_xlabel("成本")
    a.set_ylabel("收入")
    a.legend(fontsize=8.5)
    a.grid(color=GRID)
    a.set_axisbelow(True)

    plt.tight_layout()
    save_fig(fig, "ch02_paradigms.png")

    # 分布分析的时间序列（半小时流量），单独一张，教材里叫「分布-时间」
    fig, ax = plt.subplots(figsize=(9.2, 3.0), dpi=150)
    ax.plot(dist_traffic["ts"], dist_traffic["traffic"],
            color=C_MAIN, lw=1.0)
    ax.set_title("分布分析（时间）：半小时粒度流量", fontsize=11)
    ax.set_ylabel("流量")
    ax.grid(color=GRID)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_fig(fig, "ch02_dist_time.png")


def main() -> int:
    print("=" * 78)
    print("第 2 章 · 六类分析方法 + 四个基础范式")
    print("=" * 78)
    boston()
    rfm()
    loyalty()
    cohort()
    funnel()
    correlation_and_paradigms()
    print("\n全部完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
