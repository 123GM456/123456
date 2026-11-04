"""第 2 章 · 交互式看板：把六类分析结果拼成一页 HTML（pyecharts）。

教材里同一个案例在 Power BI 里是「一页报表 + 切片器联动」；
这里用 pyecharts 的 Page 复刻同样的观看顺序：
漏斗看转化 → 同期群看留存 → 忠诚度看结构 → 波士顿看品牌 → RFM 看人群。

运行：
    py -3.13 scripts/ch02_dashboard.py
产物：
    outputs/ch02_dashboard.html（离线可用，依赖 ../assets/echarts.min.js）
"""

from __future__ import annotations

import os

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Funnel, Line, Page, Pie, Scatter
from pyecharts.commons.utils import JsCode
from pyecharts.globals import CurrentConfig

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "outputs")
CurrentConfig.ONLINE_HOST = "../assets/"

# 教材原图配色（Office 默认主题色）
C_MAIN, C_ALT, C_GREEN, C_YELLOW, C_PURPLE = (
    "#4472C4", "#ED7D31", "#70AD47", "#FFC000", "#7030A0",
)
THEME = ["#4472C4", "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5", "#70AD47"]


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(OUT, name))


def base_opts(title: str, sub: str) -> opts.InitOpts:
    return opts.InitOpts(width="100%", height="360px", bg_color="white")


def funnel_chart() -> Funnel:
    df = read("ch02_funnel.csv")
    c = Funnel(init_opts=base_opts("行为漏斗", "浏览→购买"))
    c.add(
        "用户数",
        [[r["behavior"], int(r["users"])] for _, r in df.iterrows()],
        sort_="descending",
        label_opts=opts.LabelOpts(position="inside", formatter="{b} {c}"),
    )
    c.set_colors([C_MAIN, C_ALT, C_GREEN, C_YELLOW])
    c.set_global_opts(
        title_opts=opts.TitleOpts(title="行为漏斗：从浏览到购买", pos_left="center"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    return c


def cohort_chart() -> Line:
    """每日留存曲线：第 N 天当天有登录的用户占比（窗口留存见 ch02_cohort_window.csv）。"""
    df = read("ch02_cohort.csv")
    c = Line(init_opts=base_opts("同期群留存", ""))
    c.add_xaxis([f"D{int(v)}" for v in df["天数"]])
    c.add_yaxis(
        "每日留存 %",
        [round(float(v), 2) for v in df["留存率%"]],
        is_smooth=True,
        symbol_size=6,
        label_opts=opts.LabelOpts(is_show=False),
    )
    c.set_colors([C_MAIN])
    c.set_global_opts(
        title_opts=opts.TitleOpts(
            title="每日留存曲线（注册月 2020-07，1001 人）", pos_left="center"
        ),
        xaxis_opts=opts.AxisOpts(type_="category", name="注册后第 N 天",
                                 axislabel_opts=opts.LabelOpts(interval=2)),
        yaxis_opts=opts.AxisOpts(type_="value", name="当天登录占比 %",
                                 min_=0, max_=105),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    return c


def loyalty_chart() -> Pie:
    df = read("ch02_loyalty.csv")
    c = Pie(init_opts=base_opts("会员忠诚度", ""))
    c.add(
        "",
        [[r["活跃等级"], int(r["会员数"])] for _, r in df.iterrows()],
        radius=["38%", "68%"],
        center=["50%", "56%"],
        label_opts=opts.LabelOpts(formatter="{b}\n{d}%"),
    )
    c.set_colors([C_MAIN, C_ALT, C_GREEN, C_YELLOW])
    c.set_global_opts(
        title_opts=opts.TitleOpts(title="会员忠诚度分层（990 名会员）", pos_left="center"),
        legend_opts=opts.LegendOpts(orient="vertical", pos_right="2%", pos_top="14%"),
    )
    return c


def boston_chart() -> Scatter:
    df = read("ch02_boston.csv")
    c = Scatter(init_opts=base_opts("品牌波士顿矩阵", ""))
    groups = {"明星": C_ALT, "金牛": C_MAIN, "问题": C_YELLOW, "瘦狗": C_GREEN}
    for name, color in groups.items():
        g = df[df["象限"] == name]
        c.add_xaxis([round(float(v), 2) for v in g["份额"]])
        c.add_yaxis(
            name,
            [round(float(v), 2) for v in g["月环比增速"]],
            symbol_size=JsCode(
                "function(d){return Math.max(8, Math.sqrt(d[0]) * 6)}"
            ),
            label_opts=opts.LabelOpts(
                is_show=True, position="top", formatter=JsCode(
                    "function(p){return p.dataIndex}"
                ),
            ),
            itemstyle_opts=opts.ItemStyleOpts(color=color, opacity=0.75),
        )
    c.set_global_opts(
        title_opts=opts.TitleOpts(title="品牌波士顿矩阵：份额 × 月环比增速", pos_left="center"),
        xaxis_opts=opts.AxisOpts(
            type_="value", name="销售额份额 %", name_gap=26,
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
        yaxis_opts=opts.AxisOpts(
            type_="value", name="8 月对 7 月环比增速 %", name_gap=26,
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
        legend_opts=opts.LegendOpts(pos_top="8%", pos_right="2%"),
        tooltip_opts=opts.TooltipOpts(trigger="item"),
    )
    return c


def rfm_chart() -> Bar:
    df = read("ch02_rfm.csv")
    grp = (
        df["user_type"]
        .value_counts()
        .rename_axis("人群")
        .reset_index(name="人数")
        .sort_values("人数", ascending=True)
    )
    c = Bar(init_opts=base_opts("RFM 人群", ""))
    c.add_xaxis([str(v) for v in grp["人群"]])
    c.add_yaxis(
        "人数",
        [int(v) for v in grp["人数"]],
        category_gap="35%",
        label_opts=opts.LabelOpts(is_show=True, position="right"),
    )
    c.set_colors([C_MAIN])
    c.set_global_opts(
        title_opts=opts.TitleOpts(title="RFM 八类人群规模（7 178 名用户）", pos_left="center"),
        xaxis_opts=opts.AxisOpts(type_="category"),
        yaxis_opts=opts.AxisOpts(
            type_="value", name="人数",
            splitline_opts=opts.SplitLineOpts(is_show=True),
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
    )
    c.reversal_axis()
    return c


def main() -> None:
    page = Page(layout=Page.SimplePageLayout, page_title="商业数据分析 · 第 2 章看板")
    for ch in (
        funnel_chart(),
        cohort_chart(),
        loyalty_chart(),
        boston_chart(),
        rfm_chart(),
    ):
        page.add(ch)
    path = os.path.join(OUT, "ch02_dashboard.html")
    page.render(path)
    # pyecharts 默认写 CDN 地址，这里换成同目录下的本地 echarts，保证离线可用
    with open(path, "r", encoding="utf-8") as fh:
        html = fh.read()
    for cdn in ("https://assets.pyecharts.org/assets/v5/echarts.min.js",
                "https://assets.pyecharts.org/assets/v6/echarts.min.js"):
        html = html.replace(cdn, "../assets/echarts.min.js")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"看板 → {path}（5 个组件，离线可用）")


if __name__ == "__main__":
    main()
