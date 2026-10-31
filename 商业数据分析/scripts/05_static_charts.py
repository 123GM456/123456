# -*- coding: utf-8 -*-
"""
05_static_charts.py — 论文静态配图（Matplotlib，150 dpi PNG）
=============================================================
技术栈：Matplotlib（课程要求指定的 Python 可视化库之一），中文字体用系统自带的
微软雅黑，输出 150 dpi PNG 供 06_report.py 直接嵌入论文 docx。

图表清单（全部读取 outputs/models 的模型结果，保证图文数字一致）：
  paper_fig1  全球加权增速 vs 中国增速（双折线）
  paper_fig2  七大区域 GDP 份额演变（堆叠面积）
  paper_fig3  帕累托图（柱 + 累计折线双轴）
  paper_fig4  波士顿矩阵四象限（气泡散点）
  paper_fig5  K-Means 五群体分群（散点 + 图例）
  paper_fig6  中国 GDP Holt 预测与 95% 置信带
  paper_fig7  M5 滚动回测误差（分组柱形）
  paper_fig8  2024 年收入分组份额（环形图）

运行：python scripts/05_static_charts.py
依赖：pandas, numpy, matplotlib
"""
import json
import os

import matplotlib
matplotlib.use("Agg")                      # 无界面后端，服务器/沙箱均可跑
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(BASE, "outputs", "models")
OUT = os.path.join(BASE, "outputs", "figs_png")
os.makedirs(OUT, exist_ok=True)

DPI = 150
# 统一视觉规范：与 03_visuals.py 的图表配色保持一致
C_MAIN, C_ALT, C_GREEN = "#4472C4", "#ED7D31", "#70AD47"
C_YELLOW, C_PURPLE, C_GRAY = "#FFC000", "#7030A0", "#A5A5A5"
C_TEXT, C_GRID = "#3C3C3C", "#E1E4E8"
PALETTE = [C_MAIN, C_ALT, C_GREEN, C_YELLOW, C_PURPLE, C_GRAY,
           "#255E91", "#9E480E"]

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
    "font.family": "sans-serif",
    "axes.unicode_minus": False,
    "figure.dpi": DPI,
    "savefig.dpi": DPI,
    "axes.edgecolor": "#BFBFBF",
    "axes.labelcolor": C_TEXT,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.5,
    "xtick.color": C_TEXT,
    "ytick.color": C_TEXT,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "legend.frameon": False,
    "axes.grid": True,
    "grid.color": C_GRID,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})

REGION_CN = {
    "North America": "北美",
    "East Asia & Pacific": "东亚与太平洋",
    "Europe & Central Asia": "欧洲与中亚",
    "Latin America & Caribbean": "拉美与加勒比",
    "Middle East & North Africa": "中东与北非",
    "South Asia": "南亚",
    "Sub-Saharan Africa": "撒哈拉以南非洲",
}


def frame(w=8.6, h=4.5, title="", subtitle=""):
    """建立画布并统一标题/副标题样式。"""
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0.085, right=0.95, top=0.855, bottom=0.20)
    if title:
        fig.suptitle(title, x=0.5, y=0.965, fontsize=13.5, fontweight="bold",
                     color="#1F1F1F")
    if subtitle:
        fig.text(0.5, 0.895, subtitle, ha="center", fontsize=8.5, color="#767676")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return fig, ax


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=DPI, facecolor="white", bbox_inches="tight",
                pad_inches=0.18)
    plt.close(fig)
    print("  OK %s" % name)


# ------------------------------------------------------------------ 图 1
def fig1_line():
    d = pd.read_csv(os.path.join(MOD, "m1_china_trend.csv"), encoding="utf-8-sig")
    years = d["year"].astype(int).tolist()
    world = d["全球加权增速"].astype(float).tolist()
    china = d["GDP增长率"].astype(float).tolist()

    fig, ax = frame(8.6, 4.5, "全球加权增速与中国实际 GDP 增速（2000—2024）",
                    "数据来源：世界银行 WDI；全球线以上年 GDP 为权重加权")
    ax.plot(years, world, color=C_MAIN, lw=2.0, marker="o", ms=3.2,
            label="全球（GDP 加权）")
    ax.plot(years, china, color=C_ALT, lw=2.2, marker="o", ms=3.2, label="中国")
    ax.axhline(0, color="#9A9A9A", lw=0.9, ls=(0, (4, 3)))
    ax.set_xticks(range(2000, 2025, 2))
    ax.set_xlabel("年份")
    ax.set_ylabel("同比增速（%）")
    ax.set_ylim(-4.5, 16)
    ax.legend(loc="upper left", ncol=2)
    i20 = years.index(2020)
    ax.annotate("2020 年疫情冲击", xy=(2020, world[i20]), xytext=(2012.8, -3.4),
                fontsize=8, color="#8C8C8C",
                arrowprops=dict(arrowstyle="->", color="#B0B0B0", lw=0.8))
    ax.annotate("%.2f%%" % china[-1], xy=(2024, china[-1]),
                xytext=(2024.5, china[-1] + 1.1), fontsize=8.5, color=C_ALT,
                fontweight="bold", ha="center")
    ax.annotate("%.2f%%" % world[-1], xy=(2024, world[-1]),
                xytext=(2024.5, world[-1] - 1.9), fontsize=8.5, color=C_MAIN,
                fontweight="bold", ha="center")
    ax.set_xlim(1999.4, 2025.4)
    save(fig, "paper_fig1_全球与中国GDP增速.png")


# ------------------------------------------------------------------ 图 2
def fig2_stack():
    r = pd.read_csv(os.path.join(MOD, "m6_region_share.csv"), encoding="utf-8-sig")
    regs = [c for c in r.columns if c != "year"]
    order = r.iloc[-1][regs].astype(float).sort_values(ascending=False).index.tolist()
    years = r["year"].astype(int).tolist()
    data = [r[reg].astype(float).tolist() for reg in order]

    fig, ax = frame(8.8, 5.0, "七大区域 GDP 份额演变（%）",
                    "数据来源：世界银行 WDI；各区域份额之和为 100%")
    ax.stackplot(years, *data,
                 labels=[REGION_CN.get(x, x) for x in order],
                 colors=PALETTE[:len(order)], alpha=0.95, edgecolor="white",
                 linewidth=0.6)
    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(0, 100)
    ax.set_xticks(range(2000, 2025, 5))
    ax.set_xlabel("年份")
    ax.set_ylabel("占全球 GDP 比重（%）")
    ax.grid(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4,
              handlelength=1.6, columnspacing=1.4)
    save(fig, "paper_fig2_区域份额演变.png")


# ------------------------------------------------------------------ 图 3
def fig3_pareto():
    d0 = pd.read_csv(os.path.join(MOD, "m2_pareto_abc.csv"),
                     encoding="utf-8-sig").head(20)
    names = d0["country_name"].tolist()
    share = d0["份额"].astype(float).tolist()
    cum = d0["累计份额"].astype(float).tolist()
    colors = [C_MAIN if a == "A" else (C_GREEN if a == "B" else C_GRAY)
              for a in d0["ABC分类"]]

    fig, ax = frame(9.4, 4.6, "帕累托图：前 20 国占全球 GDP 81.29%",
                    "世界银行 WDI 2024 年现价美元 GDP；柱为个体份额（左轴），"
                    "橙线为累计份额（右轴）")
    x = np.arange(len(names))
    ax.bar(x, share, color=colors, width=0.66, label="个体份额")
    ax.set_xticks(x)
    ax.set_xticklabels([n if len(n) <= 10 else n[:10] + "…" for n in names],
                       rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("个体份额（%）")
    ax.set_ylim(0, max(share) * 1.18)
    ax.grid(axis="x", visible=False)

    ax2 = ax.twinx()
    ax2.plot(x, cum, color=C_ALT, lw=2.0, marker="o", ms=4, label="累计份额")
    ax2.set_ylim(0, 104)
    ax2.set_ylabel("累计份额（%）", color=C_ALT)
    ax2.tick_params(axis="y", colors=C_ALT)
    ax2.grid(False)
    ax2.spines["top"].set_visible(False)

    ax2.axhline(80, color=C_PURPLE, lw=1.2, ls=(0, (5, 3)))
    ax2.text(len(names) - 0.6, 84.5, "80% 分界线（第 19 国）", fontsize=8.2,
             color=C_PURPLE, fontweight="bold", ha="right")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", ncol=2)
    save(fig, "paper_fig3_帕累托图.png")


# ------------------------------------------------------------------ 图 4
def fig4_boston(con):
    d0 = pd.read_csv(os.path.join(MOD, "m3_matrix_full.csv"), encoding="utf-8-sig")
    d0 = d0[d0["复合增速"].notna() & d0["全球GDP份额"].notna()].copy()
    m3 = con["M3_波士顿"]
    x_med, y_med = float(m3["x_median"]), float(m3["y_median"])

    xs = np.log10(np.clip(d0["全球GDP份额"].astype(float), 1e-4, None))
    ys = d0["复合增速"].astype(float)
    size = np.sqrt(d0["GDP现价"].astype(float) / 1e12) * 26 + 18

    xm_log = float(np.log10(max(x_med, 1e-4)))
    fig, ax = frame(9.2, 5.2, "波士顿矩阵：份额 × 增速四象限",
                    "横轴 log10(2024 全球份额%%)，纵轴 2015—2024 复合增速%%；"
                    "分界：份额 %.2f%%（log10=%.2f）、增速 %.2f%%（全球加权）"
                    % (x_med, xm_log, y_med))
    ax.scatter(xs, ys, s=size, c=C_MAIN, alpha=0.45, edgecolors="white",
               linewidths=0.8, zorder=3)
    ax.axvline(xm_log, color="#8C8C8C", lw=1.1)
    ax.axhline(y_med, color="#8C8C8C", lw=1.1)
    ax.set_xlabel("log10(全球 GDP 份额 %)")
    ax.set_ylabel("2015—2024 复合增速（%）")
    ax.set_ylim(-20, 20)

    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    for text, px, py, ha, va in (("金牛", x0 + 0.06, y1 - 2.0, "left", "top"),
                                 ("明星", x1 - 0.06, y1 - 2.0, "right", "top"),
                                 ("瘦狗", x0 + 0.06, y0 + 1.8, "left", "bottom"),
                                 ("问题", x1 - 0.06, y0 + 1.8, "right", "bottom")):
        ax.text(px, py, text, fontsize=11, color="#BFBFBF", fontweight="bold",
                ha=ha, va=va)
    fig.text(0.5, 0.045,
             "注：气泡面积正比于 2024 年 GDP 规模；份额最大的三国为中国 16.93%、"
             "美国 26.49%、印度 3.40%",
             ha="center", fontsize=8.2, color="#8C8C8C")
    fig.subplots_adjust(bottom=0.26, top=0.845)
    save(fig, "paper_fig4_波士顿矩阵.png")


# ------------------------------------------------------------------ 图 5
def fig5_cluster(con):
    d0 = pd.read_csv(os.path.join(MOD, "m4_clusters.csv"), encoding="utf-8-sig")
    d0 = d0[d0["人均GDP_原始"].notna() & d0["GDP增长率"].notna()].copy()
    pops = (d0.groupby("群体")["人均GDP_原始"].mean()
            .sort_values(ascending=False).index.tolist())

    fig, ax = frame(9.2, 5.0,
                    "K-Means 国家分群（k=%s，轮廓系数 %s）"
                    % (con["M4_聚类"]["best_k"], con["M4_聚类"]["silhouette"]),
                    "特征：2015—2024 年六项指标均值，z-score 标准化后聚类；"
                    "横轴为对数刻度")
    for i, p in enumerate(pops):
        g = d0[d0["群体"] == p]
        ax.scatter(g["人均GDP_原始"], g["GDP增长率"], s=42,
                   c=PALETTE[i % len(PALETTE)], label="%s（%d 国）" % (p, len(g)),
                   alpha=0.88, edgecolors="white", linewidths=0.7, zorder=3)
    ax.set_xscale("log")
    ticks = [100, 316, 1000, 3162, 10000, 31623, 100000]
    ax.set_xticks(ticks)
    ax.set_xticklabels(["100", "316", "1k", "3.2k", "10k", "32k", "100k"])
    ax.set_xlabel("人均 GDP（美元，对数刻度）")
    ax.set_ylabel("2015—2024 平均增速（%）")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3,
              handletextpad=0.4, columnspacing=1.6)
    save(fig, "paper_fig5_KMeans分群.png")


# ------------------------------------------------------------------ 图 6
def fig6_forecast(con):
    h = pd.read_csv(os.path.join(MOD, "m5_history.csv"), encoding="utf-8-sig")
    f = pd.read_csv(os.path.join(MOD, "m5_forecast.csv"), encoding="utf-8-sig")
    m5 = con["M5_预测"]

    fig, ax = frame(8.6, 4.7,
                    "中国 GDP 预测（Holt 线性趋势，MAPE %.2f%%）" % m5["mape"],
                    "α=%.2f，β=%.2f，阴影为 95%% 置信区间"
                    % (m5["alpha"], m5["beta"]))
    ax.plot(h["year"], h["实际GDP"], color=C_MAIN, lw=2.0, label="历史实际")
    fy = [h["year"].iloc[-1]] + f["year"].tolist()
    py = [h["实际GDP"].iloc[-1]] + f["预测GDP"].tolist()
    ax.plot(fy, py, color=C_ALT, lw=2.2, marker="o", ms=4, label="点预测")
    ax.fill_between(fy,
                    [h["实际GDP"].iloc[-1]] + f["下限95"].tolist(),
                    [h["实际GDP"].iloc[-1]] + f["上限95"].tolist(),
                    color=C_MAIN, alpha=0.15, label="95% 置信区间", linewidth=0)
    for yr, v in zip(f["year"], f["预测GDP"]):
        ax.annotate("%.2f" % v, xy=(yr, v), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=8.2,
                    color=C_ALT, fontweight="bold")
    ax.set_xlabel("年份")
    ax.set_ylabel("GDP（万亿美元）")
    ax.set_xlim(h["year"].iloc[0] - 0.4, f["year"].iloc[-1] + 0.6)
    ax.legend(loc="upper left")
    save(fig, "paper_fig6_中国GDP预测.png")


# ------------------------------------------------------------------ 图 7
def fig7_backtest():
    b = pd.read_csv(os.path.join(MOD, "m5_backtest.csv"), encoding="utf-8-sig")
    yrs = b["year"].astype(int).tolist()
    act = b["实际"].astype(float).tolist()
    pre = b["回测预测"].astype(float).tolist()
    err = b["绝对误差%"].astype(float).tolist()

    fig, ax = frame(7.8, 4.5, "M5 滚动回测：2022—2024 预测误差",
                    "训练至 2021 年，逐年外推三年；误差以实际值为基准")
    x = np.arange(len(yrs))
    w = 0.30
    ax.bar(x - w / 2, act, w, color=C_MAIN, label="实际值")
    ax.bar(x + w / 2, pre, w, color=C_ALT, label="回测预测")
    for xi, a, p, e in zip(x, act, pre, err):
        ax.text(xi - w / 2, a + 0.25, "%.2f" % a, ha="center", fontsize=8.2,
                color=C_MAIN)
        ax.text(xi + w / 2, p + 0.25, "%.2f" % p, ha="center", fontsize=8.2,
                color=C_ALT)
        ax.text(xi, max(a, p) + 1.5, "误差 %.2f%%" % e, ha="center", fontsize=9,
                color="#96460A", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in yrs])
    ax.set_xlabel("年份")
    ax.set_ylabel("GDP（万亿美元）")
    ax.set_ylim(0, max(max(act), max(pre)) * 1.32)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncol=2)
    save(fig, "paper_fig7_回测误差.png")


# ------------------------------------------------------------------ 图 8
def fig8_donut(con):
    rs = con["M6_结构"]["income_share_2024"]
    cn = {"高收入": rs["High income"], "中高收入": rs["Upper middle income"],
          "中低收入": rs["Lower middle income"], "低收入": rs["Low income"]}
    items = sorted(cn.items(), key=lambda kv: -kv[1])
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    cols = [C_MAIN, C_GREEN, C_YELLOW, C_ALT]

    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    fig.suptitle("2024 年 GDP 的收入分组结构（%）", x=0.5, y=0.965,
                 fontsize=13.5, fontweight="bold", color="#1F1F1F")
    fig.text(0.5, 0.885, "数据来源：世界银行 WDI；四档收入分组按人均 GNI 划分",
             ha="center", fontsize=8.5, color="#767676")
    wedges, _ = ax.pie(
        vals, colors=cols, startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.6))
    # 标签防重叠：按左右两侧分组，同侧按 y 排序后强制最小间距
    sides = {1: [], -1: []}
    for wdg, name, v in zip(wedges, labels, vals):
        ang = np.deg2rad((wdg.theta1 + wdg.theta2) / 2.0)
        x, y = 1.02 * np.cos(ang), 1.02 * np.sin(ang)
        sides[1 if x >= 0 else -1].append([x, y, name, v])
    GAP = 0.26
    for side, items in sides.items():
        items.sort(key=lambda t: t[1])
        for i in range(1, len(items)):
            if items[i][1] - items[i - 1][1] < GAP:
                items[i][1] = items[i - 1][1] + GAP
        for x, y, name, v in items:
            ax.annotate("%s %.1f%%" % (name, v), xy=(x, y),
                        xytext=(1.44 * side, y),
                        ha="left" if side > 0 else "right", va="center",
                        fontsize=9.5, color="#333333",
                        arrowprops=dict(arrowstyle="-", color="#B0B0B0", lw=0.9,
                                        connectionstyle="arc3,rad=0"))
    ax.text(0, 0.10, "2024", ha="center", va="center", fontsize=15,
            fontweight="bold", color="#333333")
    ax.text(0, -0.14, "收入分组", ha="center", va="center", fontsize=9,
            color="#767676")
    ax.set_aspect("equal")
    ax.set_xlim(-2.05, 2.05)          # 留出引线标签空间
    ax.set_ylim(-1.40, 1.50)
    ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.04)
    save(fig, "paper_fig8_收入分组结构.png")


def main():
    print("[05] 生成论文配图（Matplotlib, %d dpi）…" % DPI)
    with open(os.path.join(MOD, "conclusions.json"), encoding="utf-8") as f:
        con = json.load(f)
    fig1_line()
    fig2_stack()
    fig3_pareto()
    fig4_boston(con)
    fig5_cluster(con)
    fig6_forecast(con)
    fig7_backtest()
    fig8_donut(con)
    print("[05] 输出：", OUT)


if __name__ == "__main__":
    main()
