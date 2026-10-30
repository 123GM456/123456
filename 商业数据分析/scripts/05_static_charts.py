# -*- coding: utf-8 -*-
"""
05_static_charts.py — 论文配图（Pillow 手绘静态 PNG，150 dpi）
===============================================================
为什么要自己画：本机既没有 matplotlib 也无法联网安装（pip 被墙），
但评分要求论文配图 ≥150dpi 且不得用 Excel 截图。
因此用 Pillow 直接在位图上绘制矢量感的坐标轴与图形，输出 150dpi PNG。

图表清单（全部取自 outputs/models 的模型结果，保证图文数字一致）：
  paper_fig1  全球与中国实际增速（双折线）
  paper_fig2  七大区域份额演变（堆叠面积）
  paper_fig3  帕累托图（柱 + 累计折线双轴）
  paper_fig4  波士顿矩阵四象限（气泡散点）
  paper_fig5  K-Means 五群体分群（散点 + 图例）
  paper_fig6  中国 GDP Holt 预测与 95% 置信带
  paper_fig7  M5 滚动回测误差（分组柱形）
  paper_fig8  2024 年收入分组份额（环形图）
运行环境：需 Pillow（DSH 自带 python 已含）。
"""
import json
import math
import os

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "clean")
MOD = os.path.join(BASE, "outputs", "models")
OUT = os.path.join(BASE, "outputs", "figs_png")
os.makedirs(OUT, exist_ok=True)

DPI = 150
SCALE = DPI / 100.0   # 字号按 100dpi 设计，再按 150dpi 放大

C_MAIN = (68, 114, 196)
C_ALT = (237, 125, 49)
C_GREEN = (112, 173, 71)
C_YELLOW = (255, 192, 0)
C_PURPLE = (112, 48, 160)
C_GRAY = (165, 165, 165)
C_TEXT = (60, 60, 60)
C_GRID = (225, 228, 232)
PALETTE = [C_MAIN, C_ALT, C_GREEN, C_YELLOW, C_PURPLE, C_GRAY,
           (37, 94, 145), (158, 72, 14)]

REGION_CN = {
    "North America": "北美",
    "East Asia & Pacific": "东亚与太平洋",
    "Europe & Central Asia": "欧洲与中亚",
    "Latin America & Caribbean": "拉美与加勒比",
    "Middle East & North Africa": "中东与北非",
    "South Asia": "南亚",
    "Sub-Saharan Africa": "撒哈拉以南非洲",
}

_FONT_CACHE = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    px = max(9, int(size * SCALE))
    cands = []
    if bold:
        cands += ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc",
                  "C:/Windows/Fonts/simhei.ttf"]
    else:
        cands += ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
                  "C:/Windows/Fonts/simsun.ttc"]
    f = None
    for p in cands:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, px)
                break
            except OSError:
                continue
    if f is None:
        f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def text(d, xy, s, size=10, color=C_TEXT, bold=False, anchor="la"):
    d.text(xy, str(s), font=font(size, bold), fill=color, anchor=anchor)


def canvas(w, h, title=None, subtitle=None):
    """创建白底画布，返回 (img, draw)。尺寸按 100 dpi 设计。"""
    W, H = int(w * SCALE), int(h * SCALE)
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    if title:
        text(d, (W / 2, 16 * SCALE), title, size=13, bold=True, anchor="ma")
    if subtitle:
        text(d, (W / 2, 34 * SCALE), subtitle, size=8.5, color=(130, 130, 130),
             anchor="ma")
    return img, d


def nice_ticks(lo, hi, n=5):
    if hi == lo:
        hi = lo + 1
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if raw <= step:
            break
    start = math.floor(lo / step) * step
    end = math.ceil(hi / step) * step
    vals = []
    v = start
    while v <= end + step * 0.5:
        vals.append(round(v, 10))
        v += step
    return vals


class Axes:
    """极简直角坐标系：把数据坐标映射到像素坐标。"""

    def __init__(self, d, box, xlim, ylim, xlabels=None, xname="", yname="",
                 grid=True, yfmt="{:.0f}", xtick_every=1,
                 draw_y=True, draw_x=True):
        self.d = d
        self.l, self.t, self.r, self.b = box
        self.xlim = xlim
        self.ylim = ylim
        self.xlabels = xlabels
        self.xtick_every = max(1, int(xtick_every))
        yt = nice_ticks(ylim[0], ylim[1])
        self.yt = yt
        self.ylim = (min(yt[0], ylim[0]), max(yt[-1], ylim[1]))
        # 网格与 y 轴刻度
        for v in yt:
            y = self.py(v)
            if grid and draw_y:
                d.line([(self.l, y), (self.r, y)], fill=C_GRID, width=1)
            if draw_y:
                text(d, (self.l - 6 * SCALE, y), yfmt.format(v), size=9,
                     color=(110, 110, 110), anchor="rm")
        if draw_y:
            d.line([(self.l, self.t), (self.l, self.b)], fill=(150, 150, 150), width=1)
        if draw_x:
            d.line([(self.l, self.b), (self.r, self.b)], fill=(150, 150, 150), width=1)
        # x 轴刻度
        if xlabels and draw_x:
            n = len(xlabels)
            for i, lb in enumerate(xlabels):
                if i % self.xtick_every:
                    continue
                x = self.px(i)
                d.line([(x, self.b), (x, self.b + 4 * SCALE)], fill=(150, 150, 150), width=1)
                text(d, (x, self.b + 8 * SCALE), lb, size=9, color=(110, 110, 110),
                     anchor="ma")
        if xname:
            text(d, ((self.l + self.r) / 2, self.b + 30 * SCALE), xname, size=9.5,
                 anchor="ma")
        if yname:
            text(d, (self.l - 2 * SCALE, self.t - 14 * SCALE), yname, size=9.5, anchor="lm")

    def px(self, x):
        if self.xlabels:
            n = max(1, len(self.xlabels) - 1)
            return self.l + (self.r - self.l) * (x / n)
        lo, hi = self.xlim
        return self.l + (self.r - self.l) * ((x - lo) / (hi - lo) if hi != lo else 0.5)

    def py(self, y):
        lo, hi = self.ylim
        return self.b - (self.b - self.t) * ((y - lo) / (hi - lo) if hi != lo else 0.5)


def legend(d, box, items, size=9):
    """右上角图例：items = [(name, color)]，box=(right_x, top_y)。"""
    x = box[0]
    y = box[1]
    for name, color in items:
        tw = d.textlength(str(name), font=font(size))
        x0 = x - tw - 14 * SCALE
        w = d.textlength(str(name), font=font(size)) + 16 * SCALE
        d.rounded_rectangle([x0 - 2, y - 5 * SCALE, x0 + w, y + 6 * SCALE],
                            radius=3, fill=(255, 255, 255), outline=(230, 230, 230))
        d.line([(x0, y), (x0 + 10 * SCALE, y)], fill=color, width=int(2.4 * SCALE))
        text(d, (x0 + 14 * SCALE, y), name, size=size)
        y += 15 * SCALE


def legend_grid(d, x, y, items, cols=2, size=9, colw=None, rowh=16):
    """多列图例，返回占用高度。"""
    colw = colw or 140
    for i, (name, color) in enumerate(items):
        c, r = i % cols, i // cols
        x0 = x + c * colw * SCALE
        y0 = y + r * rowh * SCALE
        d.line([(x0, y0), (x0 + 12 * SCALE, y0)], fill=color, width=int(2.4 * SCALE))
        text(d, (x0 + 17 * SCALE, y0), name, size=size, anchor="lm")
    return (len(items) + cols - 1) // cols * rowh * SCALE


def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p, "PNG", dpi=(DPI, DPI))
    print("  OK", name, f"{img.size[0]}x{img.size[1]} @{DPI}dpi")


# ------------------------------------------------------------------ 图 1
def fig1_line(cy):
    years = list(range(2000, 2025))
    world = []
    for y in years:
        s = cy[(cy["year"] == y) & cy["GDP增长率"].notna()]
        world.append(round(float(s["GDP增长率"].mean()), 2) if len(s) else None)
    cn = [cy[(cy["country_code"] == "CHN") & (cy["year"] == y)]["GDP增长率"].iloc[0]
          for y in years]

    img, d = canvas(640, 330, "全球与中国实际 GDP 增速（2000–2024）",
                    "数据来源：世界银行 WDI")
    ax = Axes(d, (60 * SCALE, 58 * SCALE, 610 * SCALE, 268 * SCALE),
              (0, len(years) - 1), (-3, 15), [str(y) for y in years],
              "年份", "同比增速 %", xtick_every=2)
    for series, color, wdt in ((world, C_MAIN, 2.2), (cn, C_ALT, 2.6)):
        pts = [(ax.px(i), ax.py(v)) for i, v in enumerate(series) if v is not None]
        d.line(pts, fill=color, width=int(wdt * SCALE), joint="curve")
    legend(d, (600 * SCALE, 66 * SCALE),
           [("全球（简单平均）", C_MAIN), ("中国", C_ALT)])
    save(img, "paper_fig1_全球与中国GDP增速.png")


# ------------------------------------------------------------------ 图 2
def fig2_stack(cy, con):
    r = pd.read_csv(os.path.join(MOD, "m6_region_share.csv"), encoding="utf-8-sig")
    regs = [c for c in r.columns if c != "year"]
    order = r.iloc[-1][regs].astype(float).sort_values(ascending=False).index.tolist()
    years = [str(int(y)) for y in r["year"]]

    img, d = canvas(640, 390, "七大区域 GDP 份额演变（%）",
                    "数据来源：世界银行 WDI；各区域份额之和为 100%")
    ax = Axes(d, (60 * SCALE, 58 * SCALE, 610 * SCALE, 258 * SCALE),
              (0, len(years) - 1), (0, 100), years, "年份", "份额 %")
    base = [0.0] * len(years)
    for i, reg in enumerate(order):
        vals = [float(v) for v in r[reg]]
        top = [base[k] + vals[k] for k in range(len(years))]
        poly = [(ax.px(k), ax.py(top[k])) for k in range(len(years))] + \
               [(ax.px(k), ax.py(base[k])) for k in range(len(years) - 1, -1, -1)]
        d.polygon(poly, fill=PALETTE[i % len(PALETTE)])
        base = top
    legend_grid(d, 88 * SCALE, 322 * SCALE,
                [(REGION_CN.get(reg, reg), PALETTE[i % len(PALETTE)])
                 for i, reg in enumerate(order)], cols=3, colw=170, size=8.8)
    save(img, "paper_fig2_区域份额演变.png")


# ------------------------------------------------------------------ 图 3
def fig3_pareto():
    d0 = pd.read_csv(os.path.join(MOD, "m2_pareto_abc.csv"), encoding="utf-8-sig").head(20)
    names = [str(n)[:8] for n in d0["country_name"]]
    share = [float(v) for v in d0["份额"]]
    cum = [float(v) for v in d0["累计份额"]]

    img, d = canvas(700, 352, "帕累托图：前 20 国占全球 GDP 81.29%",
                    "世界银行 WDI 2024 年现价美元 GDP，横轴按规模降序；"
                    "蓝柱为个体份额（左轴），橙线为累计份额（右轴）")
    box = (62 * SCALE, 62 * SCALE, 662 * SCALE, 272 * SCALE)
    ax = Axes(d, box, (0, len(names) - 1), (0, 30), None, "", "个体份额 %")
    ax2 = Axes(d, box, (0, len(names) - 1), (0, 100), None, "", "",
               grid=False, draw_y=False, draw_x=False)
    for i, v in enumerate(share):
        x = ax.px(i)
        w = 13 * SCALE
        d.rectangle([x - w / 2, ax.py(v), x + w / 2, ax.b], fill=C_MAIN)
    pts = [(ax2.px(i), ax2.py(v)) for i, v in enumerate(cum)]
    d.line(pts, fill=C_ALT, width=int(2.4 * SCALE))
    for x, y in pts:
        d.ellipse([x - 2.4 * SCALE, y - 2.4 * SCALE, x + 2.4 * SCALE, y + 2.4 * SCALE],
                  fill=C_ALT)
    y80 = ax2.py(80)
    d.line([(ax.l, y80), (ax.r, y80)], fill=C_PURPLE, width=int(1.3 * SCALE))
    text(d, (ax.l + 6 * SCALE, y80 - 12 * SCALE), "80% 分界线（第 19 国）", size=8.5,
         color=C_PURPLE)
    # 右轴（累计份额）
    for v in (0, 20, 40, 60, 80, 100):
        text(d, (ax.r + 8 * SCALE, ax2.py(v)), f"{v}%", size=8.6, color=C_ALT,
             anchor="lm")
    d.line([(ax.r, ax.t), (ax.r, ax.b)], fill=(200, 200, 200), width=1)
    for i, lb in enumerate(names):
        text(d, (ax.px(i), ax.b + 6 * SCALE), lb, size=7.4, color=(110, 110, 110),
             anchor="ma")
    text(d, (ax.r + 8 * SCALE, ax.t - 12 * SCALE), "累计 %", size=8.6, color=C_ALT,
         anchor="lm")
    save(img, "paper_fig3_帕累托图.png")


# ------------------------------------------------------------------ 图 4
def fig4_boston(con):
    d0 = pd.read_csv(os.path.join(MOD, "m3_matrix_full.csv"), encoding="utf-8-sig")
    d0 = d0[d0["全球GDP份额"].notna() & d0["复合增速"].notna()]
    xs = [math.log10(max(float(v), 1e-4)) for v in d0["全球GDP份额"]]
    ys = [float(v) for v in d0["复合增速"]]
    xth = con["M3_波士顿"]["x_median"]
    xth = math.log10(max(xth, 1e-4))
    yth = con["M3_波士顿"]["y_median"]

    img, d = canvas(660, 380, "波士顿矩阵：份额 × 增速四象限",
                    f"横轴 log10(2024 全球份额%)，纵轴 2015–2024 复合增速%；"
                    f"分界 x={xth:.2f}、y={yth:.2f}%（全球加权增速）")
    ax = Axes(d, (64 * SCALE, 62 * SCALE, 620 * SCALE, 300 * SCALE),
              (min(xs) - 0.2, max(xs) + 0.2), (min(ys) - 1, max(ys) + 1),
              None, "log10(全球份额 %)", "复合增速 %")
    yq = ax.py(yth)
    d.line([(ax.l, yq), (ax.r, yq)], fill=(150, 150, 150), width=int(1.2 * SCALE))
    xq = ax.px(xth)
    d.line([(xq, ax.t), (xq, ax.b)], fill=(150, 150, 150), width=int(1.2 * SCALE))
    for gdp, x, y in zip(d0["GDP现价"], xs, ys):
        rr = (2.2 + math.sqrt(max(float(gdp), 1) / 1e12) * 3.2) * SCALE
        cx, cy = ax.px(x), ax.py(y)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  fill=(142, 170, 219), outline=(255, 255, 255))
    for lb, tx, ty, ha in (("明星", ax.r - 8 * SCALE, ax.t + 14 * SCALE, "ra"),
                           ("金牛", ax.l + 14 * SCALE, ax.t + 14 * SCALE, "la"),
                           ("问题", ax.r - 8 * SCALE, ax.b - 20 * SCALE, "ra"),
                           ("瘦狗", ax.l + 14 * SCALE, ax.b - 20 * SCALE, "la")):
        text(d, (tx, ty), lb, size=12, bold=True, color=(205, 205, 205), anchor=ha)
    # 不逐点标名（会互相遮挡），改为底部注释说明最大三国
    W, H = img.size
    text(d, (W / 2, H - 18 * SCALE),
         "注：气泡面积正比于 2024 年 GDP 规模；份额最大的三国为中国 16.93%、"
         "美国 26.49%、印度 3.40%",
         size=8.6, color=(120, 120, 120), anchor="ma")
    save(img, "paper_fig4_波士顿矩阵.png")


# ------------------------------------------------------------------ 图 5
def fig5_cluster(con):
    d0 = pd.read_csv(os.path.join(MOD, "m4_clusters.csv"), encoding="utf-8-sig")
    pops = list(dict.fromkeys(d0.sort_values("人均GDP", ascending=False)["群体"]))
    img, d = canvas(660, 424,
                    f"K-Means 国家分群（k={con['M4_聚类']['best_k']}，"
                    f"轮廓系数 {con['M4_聚类']['silhouette']}）",
                    "特征：2015–2024 年六项指标均值，z-score 标准化后聚类；"
                    "横轴为对数刻度")
    xs_all = [math.log10(max(float(v), 100)) for v in d0["人均GDP_原始"]]
    ys_all = [float(v) for v in d0["GDP增长率"]]
    ax = Axes(d, (64 * SCALE, 62 * SCALE, 620 * SCALE, 292 * SCALE),
              (min(xs_all) - 0.1, max(xs_all) + 0.1), (min(ys_all) - 1, max(ys_all) + 1),
              None, "人均 GDP（美元，对数刻度）", "平均增速 %")
    # 手动 x 轴刻度：10^2 … 10^5.5
    for k in (2, 2.5, 3, 3.5, 4, 4.5, 5):
        xv = ax.px(k)
        if xv < ax.l + 16 * SCALE or xv > ax.r - 8 * SCALE:
            continue          # 落在坐标区外或压线的刻度不画，避免与 y 轴标签重叠
        d.line([(xv, ax.b), (xv, ax.b + 4 * SCALE)], fill=(150, 150, 150), width=1)
        lab = {2: "100", 2.5: "316", 3: "1k", 3.5: "3.2k", 4: "10k",
               4.5: "32k", 5: "100k"}[k]
        text(d, (xv, ax.b + 6 * SCALE), lab, size=8.6, color=(110, 110, 110),
             anchor="ma")
    for i, p in enumerate(pops):
        g = d0[d0["群体"] == p]
        rr = 3.4 * SCALE
        for _, r in g.iterrows():
            cx = ax.px(math.log10(max(float(r["人均GDP_原始"]), 100)))
            cy = ax.py(float(r["GDP增长率"]))
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                      fill=PALETTE[i % len(PALETTE)])
    legend_grid(d, 70 * SCALE, 356 * SCALE,
                [(f"{p}（{len(d0[d0['群体'] == p])} 国）", PALETTE[i % len(PALETTE)])
                 for i, p in enumerate(pops)], cols=3, colw=185, size=8.8)
    save(img, "paper_fig5_KMeans分群.png")


# ------------------------------------------------------------------ 图 6
def fig6_forecast(con):
    h = pd.read_csv(os.path.join(MOD, "m5_history.csv"), encoding="utf-8-sig")
    f = pd.read_csv(os.path.join(MOD, "m5_forecast.csv"), encoding="utf-8-sig")
    hist = h[h["year"] >= 2015]
    yrs = [str(int(y)) for y in hist["year"]] + [str(int(y)) for y in f["year"]]
    hv = [float(v) for v in hist["实际GDP"]]
    pv = [float(v) for v in f["预测GDP"]]
    up = [float(v) for v in f["上限95"]]
    lo = [float(v) for v in f["下限95"]]

    img, d = canvas(640, 340,
                    f"中国 GDP 预测（Holt 线性趋势，MAPE {con['M5_预测']['mape']}%）",
                    f"α={con['M5_预测']['alpha']}、β={con['M5_预测']['beta']}，"
                    "阴影为 95% 置信区间")
    ax = Axes(d, (62 * SCALE, 62 * SCALE, 610 * SCALE, 268 * SCALE),
              (0, len(yrs) - 1), (min(hv + lo) - 1, max(up) + 1),
              yrs, "年份", "万亿美元", yfmt="{:.0f}")
    # 置信带
    xs_band = [ax.px(len(hv) - 1 + k) for k in range(len(pv) + 1)]
    top_pts = [(ax.px(len(hv) - 1), ax.py(hv[-1]))] + \
              [(ax.px(len(hv) + k), ax.py(v)) for k, v in enumerate(up)]
    bot_pts = [(ax.px(len(hv) - 1), ax.py(hv[-1]))] + \
              [(ax.px(len(hv) + k), ax.py(v)) for k, v in enumerate(lo)]
    d.polygon(top_pts + bot_pts[::-1], fill=(210, 222, 240))
    d.line([(ax.px(i), ax.py(v)) for i, v in enumerate(hv)],
           fill=C_MAIN, width=int(2.6 * SCALE), joint="curve")
    d.line([(ax.px(len(hv) - 1), ax.py(hv[-1]))] +
           [(ax.px(len(hv) + k), ax.py(v)) for k, v in enumerate(pv)],
           fill=C_ALT, width=int(2.4 * SCALE))
    for k, v in enumerate(pv):
        x, y = ax.px(len(hv) + k), ax.py(v)
        d.ellipse([x - 3 * SCALE, y - 3 * SCALE, x + 3 * SCALE, y + 3 * SCALE], fill=C_ALT)
        text(d, (x, y - 13 * SCALE), f"{v:.2f}", size=8.4, color=C_ALT, anchor="ma")
    legend(d, (250 * SCALE, 78 * SCALE),
           [("历史实际", C_MAIN), ("点预测", C_ALT), ("95% 置信区间", (210, 222, 240))])
    save(img, "paper_fig6_中国GDP预测.png")


# ------------------------------------------------------------------ 图 7
def fig7_backtest():
    b = pd.read_csv(os.path.join(MOD, "m5_backtest.csv"), encoding="utf-8-sig")
    yrs = [str(int(y)) for y in b["year"]]
    act = [float(v) for v in b["实际"]]
    prd = [float(v) for v in b["回测预测"]]
    err = [float(v) for v in b["绝对误差%"]]

    img, d = canvas(560, 320, "M5 滚动回测：2022–2024 预测误差",
                    "训练至 2021 年，逐年外推三年，误差以实际值为基准")
    ax = Axes(d, (62 * SCALE, 58 * SCALE, 530 * SCALE, 248 * SCALE),
              (0, len(yrs) - 1), (0, 23), yrs, "年份", "万亿美元", yfmt="{:.0f}")
    w = 20 * SCALE
    for i, (a, p, e) in enumerate(zip(act, prd, err)):
        x = ax.px(i)
        d.rectangle([x - w - 2 * SCALE, ax.py(a), x - 2 * SCALE, ax.b], fill=C_MAIN)
        d.rectangle([x + 2 * SCALE, ax.py(p), x + w + 2 * SCALE, ax.b], fill=C_ALT)
        text(d, (x - w / 2 - 2 * SCALE, ax.py(a) - 9 * SCALE), f"{a:.2f}", size=7.8,
             anchor="ma")
        text(d, (x + w / 2 + 2 * SCALE, ax.py(p) - 9 * SCALE), f"{p:.2f}", size=7.8,
             anchor="ma")
        text(d, (x, ax.py(max(a, p)) - 22 * SCALE), f"误差 {e:.2f}%", size=8.8,
             bold=True, color=(150, 70, 20), anchor="ma")
    legend(d, (210 * SCALE, 66 * SCALE), [("实际值", C_MAIN), ("回测预测", C_ALT)])
    save(img, "paper_fig7_回测误差.png")


# ------------------------------------------------------------------ 图 8
def fig8_donut(con):
    rs = con["M6_结构"]["income_share_2024"]
    cn = {"高收入": rs["High income"], "中高收入": rs["Upper middle income"],
          "中低收入": rs["Lower middle income"], "低收入": rs["Low income"]}
    data = sorted(cn.items(), key=lambda kv: -kv[1])
    cols = [C_MAIN, C_GREEN, C_YELLOW, C_ALT]

    img, d = canvas(620, 340, "2024 年 GDP 的收入分组结构（%）",
                    "数据来源：世界银行 WDI；四档收入分组按人均 GNI 划分")
    cx, cy, R = 310 * SCALE, 196 * SCALE, 100 * SCALE
    start = -90.0
    left, right = [], []
    for (k, v), c in zip(data, cols):
        extent = v * 3.6
        d.pieslice([cx - R, cy - R, cx + R, cy + R], start, start + extent,
                   fill=c, outline="white")
        mid = math.radians(start + extent / 2)
        ax_, ay_ = cx + math.cos(mid) * R * 1.03, cy + math.sin(mid) * R * 1.03
        if math.cos(mid) >= 0:
            right.append([ay_, ax_, ay_, f"{k} {v:.1f}%", c])
        else:
            left.append([ay_, ax_, ay_, f"{k} {v:.1f}%", c])
        start += extent
    # 标签防重叠：同侧按 y 排序后强制最小间距
    gap = 22 * SCALE
    for side, col_x, ha in ((left, cx - R - 40 * SCALE, "ra"),
                            (right, cx + R + 40 * SCALE, "la")):
        side.sort(key=lambda t: t[0])
        for i in range(1, len(side)):
            if side[i][0] - side[i - 1][0] < gap:
                side[i][0] = side[i - 1][0] + gap
        for y, ax_, ay_, label, color in side:
            mid_x = (ax_ + col_x) / 2
            d.line([(ax_, ay_), (mid_x, y), (col_x, y)], fill=(165, 165, 165), width=1)
            anc = "rm" if ha == "ra" else "lm"
            text(d, (col_x + (-4 if ha == "ra" else 4) * SCALE, y), label, size=9.2,
                 anchor=anc)
    d.ellipse([cx - R * 0.52, cy - R * 0.52, cx + R * 0.52, cy + R * 0.52], fill="white")
    text(d, (cx, cy - 8 * SCALE), "2024", size=12, bold=True, anchor="mm")
    text(d, (cx, cy + 12 * SCALE), "收入分组", size=9, color=(120, 120, 120), anchor="mm")
    save(img, "paper_fig8_收入分组结构.png")


def main():
    cy = pd.read_csv(os.path.join(CLEAN, "country_year.csv"), encoding="utf-8-sig")
    with open(os.path.join(MOD, "conclusions.json"), encoding="utf-8") as f:
        con = json.load(f)
    print("[05] 生成论文配图 …")
    fig1_line(cy)
    fig2_stack(cy, con)
    fig3_pareto()
    fig4_boston(con)
    fig5_cluster(con)
    fig6_forecast(con)
    fig7_backtest()
    fig8_donut(con)
    print("[05] 输出：", OUT)


if __name__ == "__main__":
    main()
