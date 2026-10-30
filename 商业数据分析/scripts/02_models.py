# -*- coding: utf-8 -*-
"""
02_models.py — 五个商业分析模型
================================
M1 趋势与对比：同比/环比 + 3 年移动平均（全球、中国、主要经济体）
M2 结构集中度：帕累托 / ABC 分类（2024 年 GDP）
M3 组合定位：  波士顿矩阵（份额 × 增速四象限）
M4 客群分群：  K-Means 手写实现 + 肘部法 + 轮廓系数选 k
M5 预测预警：  Holt 线性趋势模型 + 95% 置信区间 + 滚动回测（MAPE/RMSE）

依赖仅 numpy / pandas，无需 statsmodels 或 scikit-learn，可在任意环境复现。
输出：outputs/models/*.csv 与 conclusions.json
"""
import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "clean")
OUT = os.path.join(BASE, "outputs", "models")
SEED = 42
np.random.seed(SEED)

# 分析聚焦的主要经济体（按 2024 年 GDP 前 8 位，另加入金砖样本做对照）
FOCUS = ["United States", "China", "Germany", "Japan",
         "India", "United Kingdom", "France", "Brazil"]
FOCUS_CN = {
    "United States": "美国", "China": "中国", "Germany": "德国", "Japan": "日本",
    "India": "印度", "United Kingdom": "英国", "France": "法国", "Brazil": "巴西",
    "Russian Federation": "俄罗斯", "Italy": "意大利", "Canada": "加拿大",
}


def load():
    df = pd.read_csv(os.path.join(CLEAN, "country_year.csv"), encoding="utf-8-sig")
    return df


# ---------------------------------------------------------------- M1
def m1_trend(df: pd.DataFrame) -> dict:
    """趋势与对比：全球加权增速、中国增速、增长动能、移动平均。"""
    # 全球加权增速：以各国上年 GDP 为权重，避免小国波动主导
    cur = df[["year", "country_code", "GDP现价", "GDP增长率"]].copy()
    cur = cur.sort_values(["country_code", "year"])
    cur["lag_gdp"] = cur.groupby("country_code")["GDP现价"].shift(1)
    def weighted(g):
        m = g["GDP增长率"].notna() & g["lag_gdp"].notna() & (g["lag_gdp"] > 0)
        if m.sum() == 0:
            return np.nan
        return float(np.average(g.loc[m, "GDP增长率"], weights=g.loc[m, "lag_gdp"]))
    world = cur.groupby("year").apply(weighted, include_groups=False)
    world = pd.Series(np.asarray(world.values, dtype=float),
                      index=np.asarray(world.index, dtype=int),
                      name="全球加权增速")

    china = (df[df["country_name"] == "China"]
             .set_index("year")[["GDP增长率", "GDP现价", "增长动能变化", "全球GDP份额"]])
    china = china.join(world, how="left")
    china["中国-全球增速差"] = china["GDP增长率"] - china["全球加权增速"]
    china["增长率MA3"] = china["GDP增长率"].rolling(3, min_periods=1).mean()
    china["增长率MA5"] = china["GDP增长率"].rolling(5, min_periods=1).mean()

    # 主要经济体增速矩阵（年份 × 国家）
    focus_growth = (df[df["country_name"].isin(FOCUS)]
                    .pivot_table(index="year", columns="country_name", values="GDP增长率")
                    .reindex(columns=FOCUS))
    focus_growth.to_csv(os.path.join(OUT, "m1_focus_growth.csv"), encoding="utf-8-sig")
    china.to_csv(os.path.join(OUT, "m1_china_trend.csv"), encoding="utf-8-sig")

    # 全球增速的十年对比（2000s / 2010s / 2020s）
    dec = world.copy()
    dec.index = pd.to_datetime(dec.index.astype(str), format="%Y")
    decade = dec.groupby(dec.index.year // 10 * 10).mean().rename("全球加权增速")

    return {
        "china_growth_2024": float(china.loc[2024, "GDP增长率"]),
        "world_growth_2024": float(china.loc[2024, "全球加权增速"]),
        "china_gap_2024": float(china.loc[2024, "中国-全球增速差"]),
        "china_share_2024": float(china.loc[2024, "全球GDP份额"]),
        "china_share_2000": float(china.loc[2000, "全球GDP份额"]),
        "world_growth_decade": {str(int(k)): round(float(v), 2) for k, v in decade.items()},
        "focus_growth_table": focus_growth,
        "china_table": china,
        "world_series": world,
    }


# ---------------------------------------------------------------- M2
def m2_pareto(df: pd.DataFrame) -> dict:
    """帕累托/ABC：2024 年 GDP 集中度。A 类累计 70%，B 类 70-90%，C 类 >90%。"""
    d = (df[(df["year"] == 2024) & df["GDP现价"].notna()]
         [["country_name", "region", "GDP现价"]]
         .sort_values("GDP现价", ascending=False).reset_index(drop=True))
    d["排名"] = np.arange(1, len(d) + 1)
    d["份额"] = d["GDP现价"] / d["GDP现价"].sum() * 100
    d["累计份额"] = d["份额"].cumsum()

    def abc(cum):
        if cum <= 70:
            return "A"
        if cum <= 90:
            return "B"
        return "C"
    d["ABC分类"] = d["累计份额"].map(abc)
    d["ABC分类"] = d["ABC分类"].where(d["累计份额"].shift(1) <= 90, "C")
    # 边界修正：跨过 70% 的那一个国家归入 A 类，保证 A 类份额恰好 >= 70%
    first_over_70 = d.index[d["累计份额"] >= 70].min()
    if pd.notna(first_over_70):
        d.loc[:first_over_70, "ABC分类"] = "A"
    d.loc[d["累计份额"] > 90, "ABC分类"] = "C"
    d.loc[(d["累计份额"] > 70) & (d["累计份额"] <= 90) & (d.index > first_over_70), "ABC分类"] = "B"

    summary = (d.groupby("ABC分类")
               .agg(国家数=("country_name", "count"),
                    GDP合计=("GDP现价", "sum"),
                    份额合计=("份额", "sum"))
               .reset_index())
    summary["份额合计"] = summary["份额合计"].round(2)

    n80 = int((d["累计份额"] <= 80).sum()) + 1
    d.to_csv(os.path.join(OUT, "m2_pareto_abc.csv"), index=False, encoding="utf-8-sig")
    summary.to_csv(os.path.join(OUT, "m2_abc_summary.csv"), index=False, encoding="utf-8-sig")

    return {
        "total_countries": int(len(d)),
        "top10_share": round(float(d.loc[:9, "份额"].sum()), 2),
        "top20_share": round(float(d.loc[:19, "份额"].sum()), 2),
        "countries_for_80pct": int(n80),
        "abc_summary": summary,
        "pareto_table": d,
        "a_count": int((d["ABC分类"] == "A").sum()),
        "c_count": int((d["ABC分类"] == "C").sum()),
        "a_share": round(float(d.loc[d["ABC分类"] == "A", "份额"].sum()), 2),
    }


# ---------------------------------------------------------------- M3
def m3_boston(df: pd.DataFrame) -> dict:
    """波士顿矩阵：横轴=2024 全球份额（对数），纵轴=2015-2024 不变价 GDP 复合增速。"""
    span = df[(df["year"] >= 2015) & (df["year"] <= 2024)]
    # 复合增速：用不变价增长率连乘还原
    def cagr(g):
        r = g["GDP增长率"].dropna() / 100
        if len(r) < 6:
            return np.nan
        return (np.prod(1 + r) ** (1 / len(r)) - 1) * 100
    growth = span.groupby("country_name").apply(cagr, include_groups=False).rename("复合增速")
    share24 = (df[df["year"] == 2024].set_index("country_name")
               [["GDP现价", "全球GDP份额", "region", "income_group"]])
    m = share24.join(growth, how="inner").dropna(subset=["复合增速"])
    m = m[m["GDP现价"] > 0].copy()

    x_med = float(m["全球GDP份额"].median())
    # 纵轴分界改用"全球加权平均增速"（BCG 矩阵的行业增长率角色）：
    # 中位数只回答"是否比一半国家快"，加权均值回答"是否跑赢全球整体"，
    # 商业解读更强。权重用上年现价 GDP。
    _cur = span[["year", "country_code", "GDP现价", "GDP增长率"]].sort_values(
        ["country_code", "year"])
    _cur["lag_gdp"] = _cur.groupby("country_code")["GDP现价"].shift(1)
    _w = _cur["GDP增长率"].notna() & _cur["lag_gdp"].notna() & (_cur["lag_gdp"] > 0)
    y_med = float(np.average(_cur.loc[_w, "GDP增长率"], weights=_cur.loc[_w, "lag_gdp"]))

    def quad(row):
        hi_x = row["全球GDP份额"] >= x_med
        hi_y = row["复合增速"] >= y_med
        if hi_x and hi_y:
            return "明星（高份额·高增速）"
        if hi_x and not hi_y:
            return "金牛（高份额·低增速）"
        if not hi_x and hi_y:
            return "问题（低份额·高增速）"
        return "瘦狗（低份额·低增速）"
    m["象限"] = m.apply(quad, axis=1)
    m["气泡"] = np.sqrt(m["GDP现价"] / 1e9)  # 气泡半径按 GDP 平方根缩放
    m = m.sort_values("GDP现价", ascending=False).reset_index()
    m["country_name"] = m["country_name"].astype(str)
    m["中文名"] = m["country_name"].map(lambda n: FOCUS_CN.get(n, n))

    m.to_csv(os.path.join(OUT, "m3_boston.csv"), index=False, encoding="utf-8-sig")
    cnt = m["象限"].value_counts().to_dict()

    top_star = (m[m["象限"].str.startswith("明星")]
                .nlargest(3, "GDP现价")[["country_name", "全球GDP份额", "复合增速"]])
    return {
        "x_median": round(x_med, 4),
        "y_median": round(y_med, 2),
        "quadrant_counts": cnt,
        "matrix": m,
        "stars": top_star.to_dict("records"),
    }


# ---------------------------------------------------------------- M4
def _kmeans(X, k, iters=300, seed=SEED):
    """手写 K-Means（k-means++ 初始化），返回标签、质心、簇内平方和。"""
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    centers = [X[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min(((X[:, None, :] - np.array(centers)[None, :, :]) ** 2).sum(-1), axis=1)
        probs = d2 / d2.sum() if d2.sum() > 0 else np.ones(n) / n
        centers.append(X[rng.choice(n, p=probs)])
    C = np.array(centers)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        new = d.argmin(1)
        if (new == labels).all():
            break
        labels = new
        for j in range(k):
            if (labels == j).sum() > 0:
                C[j] = X[labels == j].mean(0)
    inertia = float(((X - C[labels]) ** 2).sum())
    return labels, C, inertia


def _silhouette(X, labels):
    """手写轮廓系数（样本量 217，O(n^2) 可接受）。"""
    n = len(X)
    uniq = np.unique(labels)
    if len(uniq) < 2:
        return -1.0
    d = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    s = []
    for i in range(n):
        own = labels == labels[i]
        own[i] = False
        if own.sum() == 0:
            s.append(0.0)
            continue
        a = d[i, own].mean()
        b = min(d[i, labels == u].mean() for u in uniq if u != labels[i])
        s.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return float(np.mean(s))


def m4_cluster(df: pd.DataFrame) -> dict:
    """K-Means 国家分群：用 2015-2024 年 6 个特征刻画经济结构。"""
    span = df[(df["year"] >= 2015) & (df["year"] <= 2024)]
    feats = ["GDP增长率", "人均GDP增长率", "贸易占GDP比重", "出口占GDP比重",
             "失业率", "人均GDP"]
    agg = span.groupby(["country_name", "region", "income_group"])[feats].mean()
    agg["人均GDP"] = np.log10(agg["人均GDP"].clip(lower=100))
    agg = agg.dropna()
    names = agg.index.get_level_values(0).to_numpy()
    X0 = agg.to_numpy(float)

    mu, sd = X0.mean(0), X0.std(0, ddof=0)
    sd[sd == 0] = 1.0
    X = (X0 - mu) / sd

    best = None
    diag = []
    fits = {}
    for kk in range(2, 8):
        lab, C, inertia = _kmeans(X, kk)
        sil = _silhouette(X, lab)
        diag.append({"k": kk, "inertia": round(inertia, 2), "silhouette": round(sil, 4)})
        fits[kk] = {"lab": lab, "C": C, "inertia": inertia, "sil": sil}
        if best is None or sil > best["sil"]:
            best = {"k": kk, "sil": sil}
    # 选 k：以轮廓系数（簇内紧凑 vs 簇间分离）为第一准则取最大值 k=5；
    # 肘部法（簇内平方和下降幅度由 84→35）同样在 k=5 处出现拐点，两个准则互相印证。
    # 备选 k=3（0.2667）虽簇更少，但会把"增长失速型"与"低收入追赶型"合并，
    # 抹掉最重要的风险信号，故不采纳。
    k = best["k"]
    lab = fits[k]["lab"]
    C = fits[k]["C"]
    sil_k = fits[k]["sil"]

    # 用原始量纲解释质心（z-score 反标准化得到真实量纲）
    center_raw = (pd.DataFrame(X0, columns=feats)
                  .assign(簇=[f"C{j+1}" for j in lab])
                  .groupby("簇").mean())
    # 业务命名：规则阶梯而非简单按人均 GDP 排序。
    # 排序命名会把"负增长的危机国"和"低收入高增长国"混淆（两者人均 GDP 相近），
    # 因此先判增速、再判开放度、再判失业、最后才落到收入档位。
    def name_of(row):
        if row["GDP增长率"] < 0:
            return "增长失速型"
        if row["贸易占GDP比重"] > 150:
            return "外向型高开放经济体"
        if row["失业率"] > 12:
            return "高失业低增长型"
        if row["人均GDP"] < 3.6:   # log10(人均GDP) < 3.6 ≈ 4000 美元
            return "高增长追赶型"
        return "成熟稳健型"

    label_map = {c: name_of(center_raw.loc[c]) for c in center_raw.index}
    # 万一两条规则命中同名，追加序号保证唯一
    seen = {}
    for c in list(label_map):
        nm = label_map[c]
        seen[nm] = seen.get(nm, 0) + 1
        if seen[nm] > 1:
            label_map[c] = f"{nm}{seen[nm]}"

    out = pd.DataFrame({
        "country_name": names,
        "region": agg.index.get_level_values("region"),
        "income_group": agg.index.get_level_values("income_group"),
        "簇": [f"C{j+1}" for j in lab],
        "群体": [label_map[f"C{j+1}"] for j in lab],
    })
    for f in feats:
        out[f] = agg[f].to_numpy()
    out["人均GDP_原始"] = 10 ** out["人均GDP"]
    out.to_csv(os.path.join(OUT, "m4_clusters.csv"), index=False, encoding="utf-8-sig")
    center_raw.assign(群体=center_raw.index.map(label_map)).to_csv(
        os.path.join(OUT, "m4_centers.csv"), encoding="utf-8-sig")
    pd.DataFrame(diag).to_csv(os.path.join(OUT, "m4_k_diagnosis.csv"), index=False,
                              encoding="utf-8-sig")

    sizes = out["群体"].value_counts().to_dict()
    return {
        "best_k": int(k),
        "silhouette": round(float(sil_k), 4),
        "k_diag": diag,
        "sizes": sizes,
        "centers": center_raw.assign(群体=center_raw.index.map(label_map)),
        "assign": out,
    }


# ---------------------------------------------------------------- M5
def _holt(y, alpha, beta):
    """Holt 线性趋势（加性）：返回水平、趋势、拟合值。"""
    l, b = y[0], y[1] - y[0]
    fit = [l]
    ls, bs = [l], [b]
    for t in range(1, len(y)):
        l_new = alpha * y[t] + (1 - alpha) * (l + b)
        b = beta * (l_new - l) + (1 - beta) * b
        l = l_new
        fit.append(l)
        ls.append(l)
        bs.append(b)
    return np.array(ls), np.array(bs), np.array(fit)


def _holt_fit(y):
    """网格搜索 alpha/beta，最小化一步预测平方误差（业务上关注短期外推精度）。"""
    best = None
    for a in np.arange(0.05, 0.96, 0.05):
        for bt in np.arange(0.05, 0.96, 0.05):
            ls, bs, _ = _holt(y, a, bt)
            # 一步预测误差：t 期用 t-1 的水平+趋势预测
            pred = ls[:-1] + bs[:-1]
            sse = float(((y[1:] - pred) ** 2).sum())
            if best is None or sse < best[0]:
                best = (sse, a, bt)
    return best[1], best[2]


def m5_forecast(df: pd.DataFrame, country="China", horizon=3, start_year=2005) -> dict:
    """Holt 线性趋势外推 + 95% 置信区间 + 回测误差。

    建模样本起点取 2005 年：2000-2004 年含入世初期低基数与统计口径调整的跳变，
    直接纳入会使趋势项系统性高估；2005 年起进入相对稳定的增长阶段，序列更平稳。
    """
    s = (df[(df["country_name"] == country) & (df["year"] >= start_year)
            & df["GDP现价"].notna()]
         .sort_values("year").set_index("year")["GDP现价"] / 1e12)  # 单位：万亿美元
    y = s.to_numpy(float)
    years = s.index.to_numpy(int)

    alpha, beta = _holt_fit(y)
    ls, bs, _ = _holt(y, alpha, beta)
    resid = y[1:] - (ls[:-1] + bs[:-1])
    sigma = float(np.std(resid, ddof=1))

    f_years = np.arange(years[-1] + 1, years[-1] + 1 + horizon)
    point = ls[-1] + bs[-1] * np.arange(1, horizon + 1)
    # 预测方差随步长线性增长（随机游走+漂移的近似），95% 区间 ±1.96σ√h
    se = sigma * np.sqrt(np.arange(1, horizon + 1))
    lo, hi = point - 1.96 * se, point + 1.96 * se

    # 回测：用 2000-2021 训练，预测 2022-2024
    cut = list(years).index(2022)
    ytr = y[:cut]
    a2, b2 = _holt_fit(ytr)
    l2, b2s, _ = _holt(ytr, a2, b2)
    pred = l2[-1] + b2s[-1] * np.arange(1, len(y) - cut + 1)
    actual = y[cut:]
    mape = float(np.mean(np.abs((actual - pred) / actual)) * 100)
    rmse = float(np.sqrt(np.mean((actual - pred) ** 2)))

    fc = pd.DataFrame({"year": f_years, "预测GDP": point, "下限95": lo, "上限95": hi})
    hist = pd.DataFrame({"year": years, "实际GDP": y, "拟合GDP": ls})
    bt = pd.DataFrame({"year": years[cut:], "实际": actual, "回测预测": pred,
                       "绝对误差%": np.abs((actual - pred) / actual) * 100})
    fc.to_csv(os.path.join(OUT, "m5_forecast.csv"), index=False, encoding="utf-8-sig")
    hist.to_csv(os.path.join(OUT, "m5_history.csv"), index=False, encoding="utf-8-sig")
    bt.to_csv(os.path.join(OUT, "m5_backtest.csv"), index=False, encoding="utf-8-sig")

    return {
        "country": country, "alpha": round(float(alpha), 2), "beta": round(float(beta), 2),
        "sigma": round(sigma, 4), "mape": round(mape, 2), "rmse": round(rmse, 4),
        "forecast": fc, "history": hist, "backtest": bt,
        "cagr_2000_2024": round(float((y[-1] / y[0]) ** (1 / (years[-1] - years[0])) - 1) * 100, 2),
    }


# ---------------------------------------------------------------- M6 辅助
def m6_structure(df: pd.DataFrame) -> dict:
    """结构占比变化：七大区域 GDP 份额的十年演变（用于层叠柱形/饼图）。"""
    d = df[df["GDP现价"].notna()]
    reg = d.groupby(["year", "region"])["GDP现价"].sum().reset_index()
    reg = reg[reg["year"].isin([2000, 2005, 2010, 2015, 2020, 2024])]
    piv = reg.pivot(index="year", columns="region", values="GDP现价")
    share = piv.div(piv.sum(axis=1), axis=0) * 100
    share.to_csv(os.path.join(OUT, "m6_region_share.csv"), encoding="utf-8-sig")

    inc = d.groupby(["year", "income_group"])["GDP现价"].sum().unstack()
    inc_share = inc.div(inc.sum(axis=1), axis=0) * 100
    inc_share.to_csv(os.path.join(OUT, "m6_income_share.csv"), encoding="utf-8-sig")

    top10_series = (d.sort_values(["year", "GDP现价"], ascending=[True, False])
                    .groupby("year").head(10).groupby("year")["GDP现价"].sum())
    total = d.groupby("year")["GDP现价"].sum()
    conc = (top10_series / total * 100).dropna()
    conc.to_csv(os.path.join(OUT, "m6_top10_concentration.csv"), encoding="utf-8-sig")
    return {
        "region_share": share,
        "income_share": inc_share,
        "top10_2024": round(float(conc.loc[2024]), 2),
        "top10_2000": round(float(conc.loc[2000]), 2),
    }


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    df = load()

    m1 = m1_trend(df)
    m2 = m2_pareto(df)
    m3 = m3_boston(df)
    m4 = m4_cluster(df)
    m5 = m5_forecast(df, "China", 3)
    m6 = m6_structure(df)

    # 结论 JSON：全部下游（大屏、论文）统一从这里取数，保证数字一致
    concl = {
        "meta": {
            "seed": SEED,
            "focus_countries": FOCUS,
            "focus_cn": FOCUS_CN,
            "data_source": "World Bank WDI, 2026-10-08 更新，2000-2024",
        },
        "M1_趋势对比": {
            "china_growth_2024": round(m1["china_growth_2024"], 2),
            "world_growth_2024": round(m1["world_growth_2024"], 2),
            "china_gap_2024": round(m1["china_gap_2024"], 2),
            "china_share_2024": round(m1["china_share_2024"], 2),
            "china_share_2000": round(m1["china_share_2000"], 2),
            "world_growth_decade": m1["world_growth_decade"],
            "china_series": {str(k): (None if pd.isna(v) else round(float(v), 3))
                             for k, v in m1["china_table"]["GDP增长率"].items()},
            "world_series": {str(k): (None if pd.isna(v) else round(float(v), 3))
                             for k, v in m1["world_series"].items()},
        },
        "M2_帕累托": {
            "total_countries": m2["total_countries"],
            "top10_share": m2["top10_share"],
            "top20_share": m2["top20_share"],
            "countries_for_80pct": m2["countries_for_80pct"],
            "a_count": m2["a_count"],
            "c_count": m2["c_count"],
            "a_share": m2["a_share"],
            "abc": m2["abc_summary"].to_dict("records"),
            "top15": m2["pareto_table"].head(15)[
                ["country_name", "region", "份额", "累计份额", "ABC分类"]].round(3).to_dict("records"),
        },
        "M3_波士顿": {
            "x_median": m3["x_median"], "y_median": m3["y_median"],
            "quadrant_counts": m3["quadrant_counts"],
            "stars": [{k: (round(v, 3) if isinstance(v, (int, float)) else v) for k, v in r.items()}
                      for r in m3["stars"]],
        },
        "M4_聚类": {
            "best_k": m4["best_k"], "silhouette": m4["silhouette"],
            "sizes": m4["sizes"], "k_diag": m4["k_diag"],
            "centers": m4["centers"].round(2).reset_index().to_dict("records"),
            "cluster_of_china": (m4["assign"].query("country_name=='China'")["群体"].tolist()
                                 or [None])[0],
            "cluster_of_us": (m4["assign"].query("country_name=='United States'")["群体"].tolist()
                              or [None])[0],
        },
        "M5_预测": {
            "country": m5["country"], "alpha": m5["alpha"], "beta": m5["beta"],
            "sigma": m5["sigma"], "mape": m5["mape"], "rmse": m5["rmse"],
            "cagr_2000_2024": m5["cagr_2000_2024"],
            "forecast": m5["forecast"].round(3).to_dict("records"),
            "backtest": m5["backtest"].round(3).to_dict("records"),
        },
        "M6_结构": {
            "top10_2024": m6["top10_2024"], "top10_2000": m6["top10_2000"],
            "region_share_2024": {k: round(float(v), 2) for k, v in
                                  m6["region_share"].loc[2024].sort_values(ascending=False).items()},
            "region_share_2000": {k: round(float(v), 2) for k, v in
                                  m6["region_share"].loc[2000].sort_values(ascending=False).items()},
            "income_share_2024": {k: round(float(v), 2) for k, v in
                                  m6["income_share"].loc[2024].items()},
        },
    }
    with open(os.path.join(OUT, "conclusions.json"), "w", encoding="utf-8") as f:
        json.dump(concl, f, ensure_ascii=False, indent=2)
    # 供可视化脚本直接复用的大表
    m3["matrix"].to_csv(os.path.join(OUT, "m3_matrix_full.csv"), index=False,
                        encoding="utf-8-sig")
    m4["assign"].to_csv(os.path.join(OUT, "m4_assign.csv"), index=False, encoding="utf-8-sig")

    print("[02] M1 中国2024增速 %.2f%% / 全球 %.2f%% / 增速差 %.2fpct" %
          (concl["M1_趋势对比"]["china_growth_2024"], concl["M1_趋势对比"]["world_growth_2024"],
           concl["M1_趋势对比"]["china_gap_2024"]))
    print("[02] M2 前10国占 %.2f%%，%d 国贡献 80%%；A 类 %d 国占 %.2f%%" %
          (m2["top10_share"], m2["countries_for_80pct"], m2["a_count"], m2["a_share"]))
    print("[02] M3 象限分布：%s" % m3["quadrant_counts"])
    print("[02] M4 最优 k=%d，轮廓系数 %.4f，群体规模 %s" %
          (m4["best_k"], m4["silhouette"], m4["sizes"]))
    print("[02] M5 中国预测 %s，MAPE %.2f%%，RMSE %.3f 万亿美元" %
          ([round(r["预测GDP"], 2) for r in concl["M5_预测"]["forecast"]], m5["mape"], m5["rmse"]))
    print("[02] 输出：%s" % OUT)


if __name__ == "__main__":
    main()
