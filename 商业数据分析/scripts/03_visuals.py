# -*- coding: utf-8 -*-
"""
03_visuals.py — 图表复现与业务模型可视化
==========================================
A. 模板复现（fig01–fig14）：对照《Excel 数据可视化》30 种图表模板，复现 14 种不同图型
B. 业务模型图（fig15–fig22）：M1 趋势 / M2 帕累托 / M3 波士顿 / M4 聚类 / M5 预测 / M6 结构

全部图表使用 pyecharts 生成 HTML，并强制引用本地 assets/echarts.min.js（离线可用）。
输出：outputs/figs/figXX_名称.html
"""
import json
import os

import numpy as np
import pandas as pd

from pyecharts import options as opts
from pyecharts.charts import (Bar, Boxplot, Funnel, Gauge, HeatMap, Line,
                              Parallel, Pie, Radar, Sankey, Scatter, TreeMap)
from pyecharts.commons.utils import JsCode
from pyecharts.globals import CurrentConfig

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "clean")
FIGS = os.path.join(BASE, "outputs", "figs")
MOD = os.path.join(BASE, "outputs", "models")
os.makedirs(FIGS, exist_ok=True)

# 关键：把 pyecharts 的 CDN 前缀改成相对本地路径，保证断网可看
CurrentConfig.ONLINE_HOST = "../../assets/"

# 配色（Office 2016 主题色，与论文配色统一）
C_MAIN = "#4472C4"
C_ALT = "#ED7D31"
C_GREEN = "#70AD47"
C_YELLOW = "#FFC000"
C_PURPLE = "#7030A0"
C_GRAY = "#A5A5A5"
PALETTE = [C_MAIN, C_ALT, C_GREEN, C_YELLOW, C_PURPLE, C_GRAY, "#255E91", "#9E480E"]

REGION_CN = {
    "North America": "北美",
    "East Asia & Pacific": "东亚与太平洋",
    "Europe & Central Asia": "欧洲与中亚",
    "Latin America & Caribbean": "拉美与加勒比",
    "Middle East & North Africa": "中东与北非",
    "South Asia": "南亚",
    "Sub-Saharan Africa": "撒哈拉以南非洲",
}


def load():
    cy = pd.read_csv(os.path.join(CLEAN, "country_year.csv"), encoding="utf-8-sig")
    mc = pd.read_csv(os.path.join(CLEAN, "master.csv"), encoding="utf-8-sig")
    with open(os.path.join(MOD, "conclusions.json"), encoding="utf-8") as f:
        con = json.load(f)
    mods = {}
    for f in ["m1_focus_growth", "m1_china_trend", "m2_pareto_abc", "m2_abc_summary",
              "m3_boston", "m3_matrix_full", "m4_clusters", "m4_centers",
              "m4_k_diagnosis", "m5_forecast", "m5_history", "m5_backtest",
              "m6_region_share", "m6_income_share", "m6_top10_concentration"]:
        mods[f] = pd.read_csv(os.path.join(MOD, f + ".csv"), encoding="utf-8-sig")
    return cy, mc, con, mods


def base_opts(title, sub="数据来源：世界银行 WDI（2000–2024）", **kw):
    return opts.InitOpts(width=kw.pop("w", "900px"), height=kw.pop("h", "560px"),
                         theme=kw.pop("theme", "light"), page_title=title)


def title_opts(title, sub="数据来源：世界银行 WDI，2000–2024 年"):
    return opts.TitleOpts(
        title=title, subtitle=sub,
        title_textstyle_opts=opts.TextStyleOpts(font_size=17, font_weight="bold"),
        subtitle_textstyle_opts=opts.TextStyleOpts(font_size=11, color="#888"),
        pos_left="center", pos_top="1%",
    )


def global_opts(title, sub=None, legend=True, datazoom=False, **kw):
    g = dict(
        title_opts=title_opts(title, sub) if sub else title_opts(title),
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
    )
    if legend:
        g["legend_opts"] = opts.LegendOpts(pos_top="9%", pos_left="center")
    if datazoom:
        g["datazoom_opts"] = [opts.DataZoomOpts(range_start=0, range_end=100)]
    g.update(kw)
    return opts.GlobalOpts(**g)


def save(chart, fname):
    path = os.path.join(FIGS, fname)
    chart.render(path)
    # 双保险：若模板仍写入 CDN 绝对地址，替换为本地相对路径
    with open(path, encoding="utf-8") as f:
        html = f.read()
    for bad in ("https://assets.pyecharts.org/assets/v6/",
                "https://assets.pyecharts.org/assets/v5/",
                "https://assets.pyecharts.org/assets/"):
        html = html.replace(bad, "../../assets/")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("  OK", fname)


# ==================================================== A. 模板复现 14 张
def fig01_line(cy):
    """折线图：全球与中国实际 GDP 增速对比。"""
    d = cy[(cy["year"] >= 2000)][["year", "country_code", "GDP增长率"]]
    world = d.dropna(subset=["GDP增长率"]).groupby("year")["GDP增长率"].mean()
    cn = cy[cy["country_code"] == "CHN"].set_index("year")["GDP增长率"]
    years = list(range(2000, 2025))
    line = (
        Line(init_opts=base_opts("fig01"))
        .add_xaxis([str(y) for y in years])
        .add_yaxis("中国", [round(float(cn.get(y, np.nan)), 2) if y in cn.index else None
                          for y in years],
                   is_smooth=True, symbol_size=5,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C_ALT),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_ALT))
        .add_yaxis("全球（简单平均）", [round(float(world.get(y, np.nan)), 2) if y in world.index else None
                                for y in years],
                   is_smooth=True, symbol_size=5,
                   linestyle_opts=opts.LineStyleOpts(width=2, color=C_MAIN),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN))
        .set_global_opts(
            title_opts=title_opts("全球与中国实际 GDP 增速（2000–2024）"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            yaxis_opts=opts.AxisOpts(name="同比增速 %", splitline_opts=opts.SplitLineOpts(
                is_show=True, linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.4))),
            xaxis_opts=opts.AxisOpts(name="年份"),
        )
    )
    save(line, "fig01_折线图_全球与中国GDP增速.html")


def fig02_bar(cy):
    """渐变柱形图：2024 年 GDP 前十国家。"""
    d = cy[cy["year"] == 2024].nlargest(10, "GDP现价")
    names = [n if len(n) <= 12 else n[:11] + "…" for n in d["country_name"]]
    vals = [round(v / 1e12, 2) for v in d["GDP现价"]]
    bar = (
        Bar(init_opts=base_opts("fig02"))
        .add_xaxis(names)
        .add_yaxis("GDP（万亿美元）", vals, category_gap="40%",
                   itemstyle_opts=opts.ItemStyleOpts(
                       color=JsCode(
                           "new echarts.graphic.LinearGradient(0,0,0,1,["
                           "{offset:0,color:'#5B9BD5'},{offset:1,color:'#255E91'}])")))
        .set_global_opts(
            title_opts=title_opts("2024 年 GDP 前十国家（现价美元）"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=25, font_size=11)),
            yaxis_opts=opts.AxisOpts(name="万亿美元"),
        )
    )
    save(bar, "fig02_柱形图_2024GDP前十.html")


def fig03_stackarea(cy, mods):
    """堆叠面积图：七大区域 GDP 份额演变（宽表 year × region）。"""
    r = mods["m6_region_share"]
    years = [str(int(y)) for y in r["year"]]
    regs = [c for c in r.columns if c != "year"]
    order = (r.iloc[-1][regs].astype(float).sort_values(ascending=False).index.tolist())
    line = Line(init_opts=base_opts("fig03"))
    line.add_xaxis(years)
    for i, reg in enumerate(order):
        line.add_yaxis(REGION_CN.get(reg, reg), [round(float(v), 2) for v in r[reg]],
                       is_smooth=True, stack="total", symbol="none",
                       areastyle_opts=opts.AreaStyleOpts(opacity=0.85),
                       itemstyle_opts=opts.ItemStyleOpts(color=PALETTE[i % len(PALETTE)]),
                       linestyle_opts=opts.LineStyleOpts(width=0.5,
                                                         color=PALETTE[i % len(PALETTE)]))
    line.set_global_opts(
        title_opts=title_opts("七大区域 GDP 份额演变（%）"),
        legend_opts=opts.LegendOpts(pos_top="9%"),
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
        yaxis_opts=opts.AxisOpts(name="份额 %", max_=100),
        xaxis_opts=opts.AxisOpts(name="年份", boundary_gap=False),
    )
    save(line, "fig03_堆叠面积图_区域份额演变.html")


def fig04_donut(cy, con):
    """环形饼图：2024 年区域 GDP 份额。"""
    rs = con["M6_结构"]["region_share_2024"]
    data = sorted([(REGION_CN.get(k, k), round(v, 2)) for k, v in rs.items()],
                  key=lambda x: -x[1])
    pie = (
        Pie(init_opts=base_opts("fig04"))
        .add("", data, radius=["35%", "62%"], center=["50%", "56%"],
             label_opts=opts.LabelOpts(formatter="{b}\n{d}%"))
        .set_colors(PALETTE)
        .set_global_opts(
            title_opts=title_opts("2024 年全球 GDP 的区域结构"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c}%"),
        )
    )
    save(pie, "fig04_环形饼图_区域份额.html")


def fig05_rose(cy, con):
    """南丁格尔玫瑰图：四档收入分组 GDP 份额。"""
    rs = con["M6_结构"]["income_share_2024"]
    cn = {"High income": "高收入", "Upper middle income": "中高收入",
          "Lower middle income": "中低收入", "Low income": "低收入"}
    data = [(cn.get(k, k), round(v, 2)) for k, v in rs.items()]
    pie = (
        Pie(init_opts=base_opts("fig05"))
        .add("", data, radius=["18%", "68%"], center=["50%", "56%"], rosetype="radius")
        .set_colors([C_MAIN, C_GREEN, C_YELLOW, C_ALT])
        .set_global_opts(
            title_opts=title_opts("2024 年 GDP 的收入分组结构（玫瑰图）"),
            legend_opts=opts.LegendOpts(pos_bottom="1%"),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c}%"),
        )
    )
    save(pie, "fig05_玫瑰图_收入分组结构.html")


def fig06_scatter(cy):
    """散点图：人均 GDP 与 GDP 增速的关系（2024）。"""
    d = cy[(cy["year"] == 2024) & cy["人均GDP"].notna() & cy["GDP增长率"].notna()]
    d = d[d["人均GDP"] > 0]
    pts = [[round(float(np.log10(r["人均GDP"])), 3), round(float(r["GDP增长率"]), 2),
            float(r["GDP现价"])] for _, r in d.iterrows()]
    sc = (
        Scatter(init_opts=base_opts("fig06"))
        .add_xaxis([p[0] for p in pts])
        .add_yaxis("国家", [[p[0], p[1]] for p in pts],
                   symbol_size=9,
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN, opacity=0.65))
        .set_global_opts(
            title_opts=title_opts("人均 GDP 与 GDP 增速（2024 年，横轴取对数）"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode("function(p){return '人均GDP≈'+(Math.pow(10,p.value[0])/1000)"
                                 ".toFixed(1)+' 千美元<br/>增速 '+p.value[1]+'%';}")),
            xaxis_opts=opts.AxisOpts(name="log10(人均 GDP 美元)", type_="value",
                                     splitline_opts=opts.SplitLineOpts(
                                         is_show=True,
                                         linestyle_opts=opts.LineStyleOpts(type_="dashed", opacity=0.3))),
            yaxis_opts=opts.AxisOpts(name="GDP 增速 %", type_="value"),
        )
    )
    save(sc, "fig06_散点图_人均GDP与增速.html")


def fig07_radar(cy, con):
    """雷达图：八个主要经济体的多维对比。"""
    focus = con["meta"]["focus_cn"]
    codes = {"United States": "USA", "China": "CHN", "Germany": "DEU", "Japan": "JPN",
             "India": "IND", "United Kingdom": "GBR", "France": "FRA", "Brazil": "BRA"}
    dims = [("GDP增长率", 12, "增速%"), ("人均GDP增长率", 12, "人均增速%"),
            ("贸易占GDP比重", 400, "贸易%"), ("出口占GDP比重", 250, "出口%"),
            ("失业率", 30, "失业%"), ("人均GDP", 100000, "人均GDP$")]
    d = cy[cy["year"] == 2024].set_index("country_code")
    radar = Radar(init_opts=base_opts("fig07", w="980px", h="600px"))
    radar.add_schema(
        schema=[opts.RadarIndicatorItem(name=f"{n}", max_=m) for _, m, n in dims],
        splitarea_opt=opts.SplitAreaOpts(
            is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=0.08)),
        textstyle_opts=opts.TextStyleOpts(font_size=11),
    )
    for i, (en, _cn) in enumerate(focus.items()):
        code = codes.get(en)
        if code not in d.index:
            continue
        row = d.loc[code]
        vals = []
        for f, mx, _ in dims:
            v = row.get(f, np.nan)
            vals.append(round(float(v) if pd.notna(v) else 0.0, 2))
        radar.add(focus[en], [vals], color=PALETTE[i % len(PALETTE)],
                  areastyle_opts=opts.AreaStyleOpts(opacity=0.08),
                  linestyle_opts=opts.LineStyleOpts(width=2))
    radar.set_global_opts(
        title_opts=title_opts("八大经济体经济结构雷达图（2024）"),
        legend_opts=opts.LegendOpts(pos_top="9%", type_="scroll"),
    )
    save(radar, "fig07_雷达图_八国多维对比.html")


def fig08_heatmap(cy, con):
    """热力图：八个主要经济体 2000–2024 年增速。"""
    codes = ["USA", "CHN", "DEU", "JPN", "IND", "GBR", "FRA", "BRA"]
    cn = {"USA": "美国", "CHN": "中国", "DEU": "德国", "JPN": "日本",
          "IND": "印度", "GBR": "英国", "FRA": "法国", "BRA": "巴西"}
    years = list(range(2000, 2025))
    sub = cy[cy["country_code"].isin(codes) & cy["year"].isin(years)]
    piv = sub.pivot_table(index="country_code", columns="year", values="GDP增长率")
    data = []
    vmax = 0
    for yi, c in enumerate(codes):
        for xi, y in enumerate(years):
            v = piv.loc[c, y] if c in piv.index and y in piv.columns else np.nan
            if pd.notna(v):
                v = round(float(v), 2)
                vmax = max(vmax, abs(v))
                data.append([xi, yi, v])
    hm = (
        HeatMap(init_opts=base_opts("fig08", w="1000px", h="480px"))
        .add_xaxis([str(y) for y in years])
        .add_yaxis("", [cn[c] for c in codes], data, label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            title_opts=title_opts("八大经济体逐年增速热力图（%）"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(formatter=JsCode(
                "function(p){return p.value[2]+'%';}")),
            xaxis_opts=opts.AxisOpts(type_="category", splitarea_opts=opts.SplitAreaOpts(
                is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=0.3))),
            yaxis_opts=opts.AxisOpts(type_="category", splitarea_opts=opts.SplitAreaOpts(
                is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=0.3))),
            visualmap_opts=opts.VisualMapOpts(
                min_=-round(vmax), max_=round(vmax), is_calculable=True,
                orient="horizontal", pos_bottom="2%", pos_left="center",
                range_color=["#255E91", "#5B9BD5", "#FFFFFF", "#FFC000", "#C00000"]),
        )
    )
    save(hm, "fig08_热力图_八国增速.html")


def fig09_boxplot(cy):
    """箱线图：2024 年各区域增速分布（离群点识别）。"""
    d = cy[(cy["year"] == 2024) & cy["GDP增长率"].notna()]
    cats, box, outliers = [], [], []
    for reg, g in d.groupby("region"):
        v = np.sort(g["GDP增长率"].to_numpy(float))
        if len(v) < 5:
            continue
        idx = len(cats)
        cats.append(REGION_CN.get(reg, reg))
        q1, med, q3 = np.percentile(v, [25, 50, 75])
        iqr = q3 - q1
        lo = v[v >= q1 - 1.5 * iqr].min()
        hi = v[v <= q3 + 1.5 * iqr].max()
        box.append([round(float(lo), 2), round(float(q1), 2), round(float(med), 2),
                    round(float(q3), 2), round(float(hi), 2)])
        outliers.extend([[idx, round(float(x), 2)] for x in v if x < lo or x > hi])
    bp = (
        Boxplot(init_opts=base_opts("fig09"))
        .add_xaxis(cats)
        .add_yaxis("增速分布", bp_prepare(box), itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN))
        .set_global_opts(
            title_opts=title_opts("2024 年各区域 GDP 增速分布（箱线图）"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=20, font_size=11)),
            yaxis_opts=opts.AxisOpts(name="增速 %"),
        )
    )
    if outliers:
        sc = (Scatter().add_xaxis(cats)
              .add_yaxis("离群点", outliers, symbol_size=7,
                         itemstyle_opts=opts.ItemStyleOpts(color=C_ALT)))
        bp.overlap(sc)
    save(bp, "fig09_箱线图_区域增速分布.html")


def bp_prepare(vals):
    """把 [min,Q1,median,Q3,max] 转成 pyecharts BoxPlot 需要的 5 元组列表。"""
    return [[v[0], v[1], v[2], v[3], v[4]] for v in vals]


def fig10_gauge(con):
    """仪表盘：全球 GDP 集中度 / 中国份额两个指针。"""
    g1 = (
        Gauge(init_opts=base_opts("fig10", w="900px", h="420px"))
        .add("前 10 国集中度", [("前10国占全球GDP", con["M2_帕累托"]["top10_share"])],
             min_=0, max_=100, split_number=5,
             axisline_opts=opts.AxisLineOpts(
                 linestyle_opts=opts.LineStyleOpts(width=18, color=[
                     (0.5, C_GREEN), (0.75, C_YELLOW), (1, C_ALT)])),
             detail_label_opts=opts.LabelOpts(formatter="{value}%", font_size=22),
             center=["25%", "58%"], radius="40%")
        .add("中国份额", [("中国占全球GDP", con["M1_趋势对比"]["china_share_2024"])],
             min_=0, max_=100, split_number=5,
             axisline_opts=opts.AxisLineOpts(
                 linestyle_opts=opts.LineStyleOpts(width=18, color=[
                     (0.5, C_GREEN), (0.75, C_YELLOW), (1, C_ALT)])),
             detail_label_opts=opts.LabelOpts(formatter="{value}%", font_size=22),
             center=["75%", "58%"], radius="40%")
        .set_global_opts(
            title_opts=title_opts("集中度仪表盘：前 10 国集中度 vs 中国份额"),
            legend_opts=opts.LegendOpts(pos_top="8%"),
        )
    )
    save(g1, "fig10_仪表盘_集中度.html")


def fig11_treemap(cy):
    """矩形树图：2024 年 GDP 按区域 → 国家两级下钻。"""
    d = cy[(cy["year"] == 2024) & cy["GDP现价"].notna()].copy()
    d["区域"] = d["region"].map(lambda r: REGION_CN.get(r, r))
    data = []
    for reg, g in d.groupby("区域"):
        children = [{"name": r["country_name"], "value": round(float(r["GDP现价"]) / 1e9, 1)}
                    for _, r in g.nlargest(12, "GDP现价").iterrows()]
        data.append({"name": reg, "value": round(float(g["GDP现价"].sum()) / 1e9, 1),
                     "children": children})
    tm = (
        TreeMap(init_opts=base_opts("fig11", w="960px", h="560px"))
        .add("GDP", data, leaf_depth=2, roam=False,
             label_opts=opts.LabelOpts(formatter="{b}", font_size=11))
        .set_global_opts(
            title_opts=title_opts("2024 年全球 GDP 的区域-国家矩形树图（十亿美元）"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(formatter="{b}: {c} 十亿美元"),
        )
    )
    tm.set_colors(PALETTE)
    save(tm, "fig11_矩形树图_区域国家下钻.html")


def fig12_sankey(cy, con):
    """桑基图：收入分组 → 区域的 GDP 流向。"""
    d = cy[(cy["year"] == 2024) & cy["GDP现价"].notna()].copy()
    cn_inc = {"High income": "高收入", "Upper middle income": "中高收入",
              "Lower middle income": "中低收入", "Low income": "低收入"}
    nodes, links = [], {}
    for _, r in d.iterrows():
        s = cn_inc.get(r["income_group"], r["income_group"])
        t = REGION_CN.get(r["region"], r["region"]) + " "
        links[(s, t)] = links.get((s, t), 0) + float(r["GDP现价"]) / 1e9
    src = sorted({k[0] for k in links})
    dst = sorted({k[1] for k in links})
    nodes = [{"name": n} for n in src + dst]
    data = [{"source": k[0], "target": k[1], "value": round(v, 1)}
            for k, v in links.items() if v > 0]
    sk = (
        Sankey(init_opts=base_opts("fig12", w="960px", h="580px"))
        .add("GDP 流向", nodes, data, node_gap=12, node_width=16,
             linestyle_opt=opts.LineStyleOpts(opacity=0.35, curve=0.5),
             label_opts=opts.LabelOpts(font_size=11))
        .set_global_opts(
            title_opts=title_opts("收入分组 → 区域的 GDP 流向（十亿美元，2024）"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
        )
    )
    save(sk, "fig12_桑基图_收入到区域.html")


def fig13_funnel(con):
    """漏斗图：ABC 分类的累计份额收敛过程。"""
    abc = con["M2_帕累托"]["abc"]
    data = [(f"{a['ABC分类']} 类（{a['国家数']} 国）", round(a["份额合计"], 2)) for a in abc]
    fn = (
        Funnel(init_opts=base_opts("fig13", w="880px", h="440px"))
        .add("份额", data, sort_="descending", gap=3,
             label_opts=opts.LabelOpts(is_show=True, position="inside",
                                       formatter="{b}: {c}%"))
        .set_colors([C_ALT, C_YELLOW, C_MAIN])
        .set_global_opts(
            title_opts=title_opts("ABC 分类漏斗：A 类 12 国吃掉 70% 的 GDP"),
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c}%"),
        )
    )
    save(fn, "fig13_漏斗图_ABC分类.html")


def fig14_parallel(mods):
    """平行坐标图：五个聚类群体的六维画像（每个群体一条折线，便于对比形状）。"""
    c = mods["m4_centers"].copy()
    c = c.sort_values("人均GDP", ascending=False).reset_index(drop=True)
    dims = ["GDP增长率", "人均GDP增长率", "贸易占GDP比重", "出口占GDP比重", "失业率", "人均GDP"]
    names = ["GDP增速%", "人均增速%", "贸易占比%", "出口占比%", "失业率%", "log人均GDP"]
    pa = (
        Parallel(init_opts=base_opts("fig14", w="980px", h="540px"))
        .add_schema(
            [opts.ParallelAxisOpts(dim=i, name=names[i], name_location="middle",
                                   name_gap=34, is_scale=True)
             for i in range(len(dims))])
        .set_global_opts(
            title_opts=title_opts("K-Means 五个群体的六维平行坐标（质心画像）"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
        )
    )
    for i in range(len(c)):
        row = c.iloc[i]
        pa.add(f"{row['群体']}（{row['簇']}）",
               [[round(float(row[d]), 3) for d in dims]],
               linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.9))
    pa.set_colors([C_MAIN, C_ALT, C_GREEN, C_YELLOW, C_PURPLE])
    save(pa, "fig14_平行坐标图_聚类画像.html")


# ==================================================== B. 业务模型图 8 张
def fig15_m1_dual(cy, con):
    """双轴组合图（M1）：中国增速 vs 全球份额。"""
    years = list(range(2000, 2025))
    cn = cy[cy["country_code"] == "CHN"].set_index("year")
    bar = (
        Bar(init_opts=base_opts("fig15"))
        .add_xaxis([str(y) for y in years])
        .add_yaxis("中国 GDP 增速 %", [round(float(cn.loc[y, "GDP增长率"]), 2)
                                   if y in cn.index else None for y in years],
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN),
                   yaxis_index=0, bar_max_width=26)
        .extend_axis(yaxis=opts.AxisOpts(name="全球份额 %", position="right",
                                         axisline_opts=opts.AxisLineOpts(
                                             linestyle_opts=opts.LineStyleOpts(color=C_ALT)),
                                         axislabel_opts=opts.LabelOpts(formatter="{value}%")))
        .set_global_opts(
            title_opts=title_opts("M1 中国增速与全球份额：增速换挡，份额仍升"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            yaxis_opts=opts.AxisOpts(name="增速 %"),
            xaxis_opts=opts.AxisOpts(name="年份"),
        )
    )
    line = (
        Line()
        .add_xaxis([str(y) for y in years])
        .add_yaxis("中国全球份额 %", [round(float(cn.loc[y, "全球GDP份额"]), 2)
                                 if y in cn.index and pd.notna(cn.loc[y, "全球GDP份额"]) else None
                                 for y in years],
                   yaxis_index=1, is_smooth=True, symbol_size=5,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C_ALT),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_ALT))
    )
    bar.overlap(line)
    save(bar, "fig15_M1双轴图_中国增速与份额.html")


def fig16_m2_pareto(mods, con):
    """帕累托图（M2）：柱 + 累计占比双轴。"""
    d = mods["m2_pareto_abc"]
    top = d.head(20)
    names = [n if len(n) <= 10 else n[:9] + "…" for n in top["country_name"]]
    bar = (
        Bar(init_opts=base_opts("fig16", w="980px"))
        .add_xaxis(names)
        .add_yaxis("份额 %", [round(float(v), 2) for v in top["份额"]],
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN), bar_max_width=30)
        .extend_axis(yaxis=opts.AxisOpts(name="累计份额 %", min_=0, max_=100,
                                         axislabel_opts=opts.LabelOpts(formatter="{value}%")))
        .set_global_opts(
            title_opts=title_opts("M2 帕累托图：前 20 国占全球 GDP 81.29%"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30, font_size=10)),
            yaxis_opts=opts.AxisOpts(name="份额 %"),
        )
    )
    line = (
        Line()
        .add_xaxis(names)
        .add_yaxis("累计份额 %", [round(float(v), 2) for v in top["累计份额"]],
                   yaxis_index=1, is_smooth=True, symbol_size=6,
                   linestyle_opts=opts.LineStyleOpts(width=2.5, color=C_ALT),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_ALT),
                   markline_opts=opts.MarkLineOpts(
                       data=[opts.MarkLineItem(y=80, name="80% 分界线")],
                       linestyle_opts=opts.LineStyleOpts(type_="dashed", color=C_PURPLE),
                       label_opts=opts.LabelOpts(formatter="80% 分界")))
    )
    bar.overlap(line)
    save(bar, "fig16_M2帕累托图.html")


def fig17_m2_abc(mods):
    """堆叠条形图（M2）：ABC 三类国家数与份额对比。"""
    s = mods["m2_abc_summary"]
    abc = ["A", "B", "C"]
    s = s.set_index("ABC分类").loc[abc]
    bar = (
        Bar(init_opts=base_opts("fig17"))
        .add_xaxis([f"{a} 类" for a in abc])
        .add_yaxis("国家数（个）", [int(v) for v in s["国家数"]],
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN), bar_max_width=50)
        .add_yaxis("份额（%）", [round(float(v), 2) for v in s["份额合计"]],
                   itemstyle_opts=opts.ItemStyleOpts(color=C_ALT), bar_max_width=50)
        .set_global_opts(
            title_opts=title_opts("M2 ABC 分类：数量与份额的反向分布"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            yaxis_opts=opts.AxisOpts(name="数量 / 份额"),
        )
    )
    save(bar, "fig17_M2ABC分类对比.html")


def fig18_m3_boston(mods):
    """气泡图（M3）：波士顿矩阵。"""
    d = mods["m3_matrix_full"]
    d = d[d["全球GDP份额"].notna() & d["复合增速"].notna()]
    groups = {}
    for _, r in d.iterrows():
        q = r["象限"]
        x = round(float(np.log10(max(r["全球GDP份额"], 1e-4))), 3)
        groups.setdefault(q, []).append(
            [x, round(float(r["复合增速"]), 2), round(float(r["气泡"]), 1), r["country_name"]])
    sc = Scatter(init_opts=base_opts("fig18", w="980px", h="600px"))
    sc.add_xaxis([0])
    for i, (q, pts) in enumerate(sorted(groups.items())):
        sc.add_yaxis(q.split("（")[0], [[p[0], p[1], p[2], p[3]] for p in pts],
                     symbol_size=JsCode("function(v){return Math.max(6, v[2]*0.55);}"),
                     itemstyle_opts=opts.ItemStyleOpts(color=PALETTE[i], opacity=0.7),
                     label_opts=opts.LabelOpts(is_show=False))
    x_med = float(np.log10(max(mods["m3_matrix_full"]["全球GDP份额"].median(), 1e-4)))
    sc.set_global_opts(
        title_opts=title_opts("M3 波士顿矩阵：份额 × 增速四象限（气泡=GDP 规模）"),
        legend_opts=opts.LegendOpts(pos_top="9%"),
        tooltip_opts=opts.TooltipOpts(formatter=JsCode(
            "function(p){return p.seriesName+'<br/>'+p.value[3]+'<br/>份额(log10) '+"
            "p.value[0]+'<br/>复合增速 '+p.value[1]+'%';}")),
        xaxis_opts=opts.AxisOpts(name="log10(全球份额%)", type_="value", min_=-4,
                                 splitline_opts=opts.SplitLineOpts(
                                     is_show=True,
                                     linestyle_opts=opts.LineStyleOpts(type_="dashed"))),
        yaxis_opts=opts.AxisOpts(name="2015–2024 复合增速 %", type_="value"),
        visualmap_opts=None,
    )
    save(sc, "fig18_M3波士顿矩阵.html")


def fig19_m4_cluster(mods, con):
    """分组散点图（M4）：人均 GDP × 增速，按群体着色。"""
    d = mods["m4_clusters"]
    pops = list(dict.fromkeys(d.sort_values("人均GDP", ascending=False)["群体"]))
    sc = Scatter(init_opts=base_opts("fig19", w="980px", h="580px"))
    sc.add_xaxis([0])
    for i, p in enumerate(pops):
        g = d[d["群体"] == p]
        sc.add_yaxis(f"{p}（{len(g)} 国）",
                     [[round(float(np.log10(max(r["人均GDP_原始"], 100))), 3),
                       round(float(r["GDP增长率"]), 2), r["country_name"]]
                      for _, r in g.iterrows()],
                     symbol_size=10,
                     itemstyle_opts=opts.ItemStyleOpts(color=PALETTE[i % len(PALETTE)],
                                                       opacity=0.72),
                     label_opts=opts.LabelOpts(is_show=False))
    sc.set_global_opts(
        title_opts=title_opts(f"M4 K-Means 国家分群（k={con['M4_聚类']['best_k']}，"
                              f"轮廓系数 {con['M4_聚类']['silhouette']}）"),
        legend_opts=opts.LegendOpts(pos_top="9%", type_="scroll"),
        tooltip_opts=opts.TooltipOpts(formatter=JsCode(
            "function(p){return p.seriesName+'<br/>'+p.value[2]+'<br/>人均GDP≈'"
            "+(Math.pow(10,p.value[0])/1000).toFixed(1)+' 千美元<br/>增速 '+p.value[1]+'%';}")),
        xaxis_opts=opts.AxisOpts(name="log10(人均 GDP 美元)", type_="value"),
        yaxis_opts=opts.AxisOpts(name="2015–2024 平均增速 %", type_="value"),
    )
    save(sc, "fig19_M4聚类散点.html")


def fig20_m4_k(mods):
    """双轴折线（M4）：肘部法 + 轮廓系数选 k。"""
    d = mods["m4_k_diagnosis"]
    ks = [str(int(k)) for k in d["k"]]
    line = (
        Line(init_opts=base_opts("fig20"))
        .add_xaxis(ks)
        .add_yaxis("簇内平方和 SSE", [round(float(v), 2) for v in d["inertia"]],
                   is_smooth=True, symbol_size=7, yaxis_index=0,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C_MAIN),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN))
        .extend_axis(yaxis=opts.AxisOpts(name="轮廓系数", position="right", min_=0.15, max_=0.35,
                                         axislabel_opts=opts.LabelOpts(formatter="{value}")))
        .set_global_opts(
            title_opts=title_opts("M4 选 k 的两个准则：肘部法 + 轮廓系数"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            xaxis_opts=opts.AxisOpts(name="簇数 k", type_="category"),
            yaxis_opts=opts.AxisOpts(name="SSE"),
        )
    )
    line2 = (
        Line()
        .add_xaxis(ks)
        .add_yaxis("轮廓系数", [round(float(v), 4) for v in d["silhouette"]],
                   yaxis_index=1, is_smooth=True, symbol_size=7,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C_ALT),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_ALT),
                   markline_opts=opts.MarkLineOpts(
                       data=[opts.MarkLineItem(type_="max", name="最大值")],
                       linestyle_opts=opts.LineStyleOpts(type_="dashed", color=C_PURPLE)))
    )
    line.overlap(line2)
    save(line, "fig20_M4选k诊断.html")


def fig21_m5_forecast(mods, con):
    """折线 + 置信带（M5）：中国 GDP 预测。"""
    h = mods["m5_history"]
    f = mods["m5_forecast"]
    yrs = [str(int(y)) for y in h["year"]][-8:] + [str(int(y)) for y in f["year"]]
    hist = [round(float(v), 2) for v in h["实际GDP"]][-8:] + [None] * len(f)
    # 预测序列从最后一个历史点起笔，使虚线与实线在 2024 处衔接
    pred = [None] * 7 + [hist[-1]] + [round(float(v), 2) for v in f["预测GDP"]]
    up = [None] * 7 + [hist[-1]] + [round(float(v), 2) for v in f["上限95"]]
    lo = [None] * 7 + [hist[-1]] + [round(float(v), 2) for v in f["下限95"]]
    line = (
        Line(init_opts=base_opts("fig21", w="960px", h="520px"))
        .add_xaxis(yrs)
        .add_yaxis("历史实际", hist, is_smooth=True, symbol_size=6,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C_MAIN),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN))
        .add_yaxis("Holt 点预测", pred, is_smooth=False, symbol_size=8,
                   linestyle_opts=opts.LineStyleOpts(width=3, type_="dashed", color=C_ALT),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_ALT),
                   label_opts=opts.LabelOpts(is_show=True, position="top",
                                             formatter="{c} 万亿"))
        .add_yaxis("95% 置信上限", up, symbol="none",
                   linestyle_opts=opts.LineStyleOpts(width=1, type_="dotted", color=C_GRAY),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_GRAY))
        .add_yaxis("95% 置信下限", lo, symbol="none",
                   linestyle_opts=opts.LineStyleOpts(width=1, type_="dotted", color=C_GRAY),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_GRAY))
        .set_global_opts(
            title_opts=title_opts(
                f"M5 中国 GDP 预测（Holt，α={con['M5_预测']['alpha']}，"
                f"β={con['M5_预测']['beta']}，MAPE={con['M5_预测']['mape']}%）"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(name="年份"),
            yaxis_opts=opts.AxisOpts(name="万亿美元"),
        )
    )
    save(line, "fig21_M5预测置信区间.html")


def fig22_m5_backtest(mods, con):
    """误差柱形图 + 折线（M5）：回测对比。"""
    b = mods["m5_backtest"]
    yrs = [str(int(y)) for y in b["year"]]
    bar = (
        Bar(init_opts=base_opts("fig22", w="900px", h="480px"))
        .add_xaxis(yrs)
        .add_yaxis("实际", [round(float(v), 2) for v in b["实际"]],
                   itemstyle_opts=opts.ItemStyleOpts(color=C_MAIN), bar_max_width=40)
        .add_yaxis("回测预测", [round(float(v), 2) for v in b["回测预测"]],
                   itemstyle_opts=opts.ItemStyleOpts(color=C_ALT), bar_max_width=40)
        .extend_axis(yaxis=opts.AxisOpts(name="绝对误差 %", position="right",
                                         min_=0, max_=20,
                                         axislabel_opts=opts.LabelOpts(formatter="{value}%")))
        .set_global_opts(
            title_opts=title_opts(f"M5 滚动回测：2022–2024 误差（RMSE "
                                  f"{con['M5_预测']['rmse']} 万亿美元）"),
            legend_opts=opts.LegendOpts(pos_top="9%"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            yaxis_opts=opts.AxisOpts(name="万亿美元"),
        )
    )
    line = (
        Line()
        .add_xaxis(yrs)
        .add_yaxis("绝对误差 %", [round(float(v), 2) for v in b["绝对误差%"]],
                   yaxis_index=1, is_smooth=True, symbol_size=8,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C_PURPLE),
                   itemstyle_opts=opts.ItemStyleOpts(color=C_PURPLE))
    )
    bar.overlap(line)
    save(bar, "fig22_M5回测误差.html")


def main():
    cy, mc, con, mods = load()
    print("[03] 生成图表 …")
    fig01_line(cy)
    fig02_bar(cy)
    fig03_stackarea(cy, mods)
    fig04_donut(cy, con)
    fig05_rose(cy, con)
    fig06_scatter(cy)
    fig07_radar(cy, con)
    fig08_heatmap(cy, con)
    fig09_boxplot(cy)
    fig10_gauge(con)
    fig11_treemap(cy)
    fig12_sankey(cy, con)
    fig13_funnel(con)
    fig14_parallel(mods)
    fig15_m1_dual(cy, con)
    fig16_m2_pareto(mods, con)
    fig17_m2_abc(mods)
    fig18_m3_boston(mods)
    fig19_m4_cluster(mods, con)
    fig20_m4_k(mods)
    fig21_m5_forecast(mods, con)
    fig22_m5_backtest(mods, con)
    print("[03] 图表输出：", FIGS)


if __name__ == "__main__":
    main()
