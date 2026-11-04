"""生成一个纯静态总览页 outputs/index.html。

为什么需要它：本项目的产物是 12 张 PNG + 38 个 csv + 1 个交互看板，
散在 outputs/ 里不好浏览，答辩或自查时想「一页看完」。
这个页面不依赖任何 JS 库（除看板本身），双击就能在浏览器里打开全部图表。

运行：py -3.13 scripts/build_index.py
"""

from __future__ import annotations

import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")

# (文件名, 章节, 图表标题, 一句话说明)
FIGURES = [
    ("ch01_schema.png", "第 1 章", "星型模型与地区结构",
     "左：交易额前 12 的地区；右：年龄段 × 性别交易额"),
    ("ch02_paradigms.png", "第 2 章", "趋势 / 构成 / 分布 / 关系四范式",
     "四种基础分析方法各一张：年度订单量、产品销量占比、用户年龄分布、成本-收入散点"),
    ("ch02_trend_week.png", "第 2 章", "周度处理时长与预警线",
     "week11 达 39 小时，超出 35 小时预警线，比均值 23.9 高 63%"),
    ("ch02_boston.png", "第 2 章", "品牌波士顿矩阵",
     "横轴份额、纵轴 8 月对 7 月环比增速；A/F/C 为明星品牌"),
    ("ch02_rfm.png", "第 2 章", "RFM 八类人群分布",
     "观测日 2019-08-03，与教材参考答案比对 R 100% / M 100%"),
    ("ch02_loyalty.png", "第 2 章", "会员忠诚度分层",
     "990 名会员按距今天数分为活跃 / 沉睡 / 流失预警 / 已流失"),
    ("ch02_cohort.png", "第 2 章", "同期群留存曲线与窗口校验",
     "左：每日留存 D0→D30；右：窗口留存与教材矩阵逐格对齐（偏差 0.00 个百分点）"),
    ("ch02_funnel.png", "第 2 章", "行为漏斗与 AARRR 漏斗",
     "浏览 100 → 收藏 90 → 加购 80 → 购买 80；AARRR 五环节"),
    ("ch02_dist_time.png", "第 2 章", "半小时粒度流量分布",
     "教材「分布分析-时间」案例的时序还原"),
    ("ch05_bank_kpi.png", "第 5 章", "银行销售 KPI 四视图",
     "风险等级销售额、收入段客单价、年龄段利润率、购买目的 Top6"),
    ("ch09_profile.png", "第 9 章", "用户画像四视图",
     "性别构成、余额分层、活跃度分层、发卡年龄分布（均值 38.3 岁）"),
    ("ch10_decompose.png", "第 10 章", "乘法效应分解与 12 期预报",
     "Y = T × S × I；旺季 7 月季节指数 1.237，回测 MAPE 9.56%"),
]

# 结果 csv 按章节归组，只做「有哪些文件」的索引，不渲染内容
CSV_GROUPS = {
    "第 1 章 关系模型": ["ch01_by_district", "ch01_by_segment",
                    "ch01_by_frequency", "ch01_by_loan_status"],
    "第 2 章 Excel 公式": ["ch02_if", "ch02_vlookup", "ch02_countif",
                      "ch02_pivot", "ch02_sumif_by_subject", "ch02_sumif_cross"],
    "第 2 章 六类分析方法": ["ch02_boston", "ch02_rfm", "ch02_rfm_compare",
                      "ch02_loyalty", "ch02_cohort", "ch02_funnel",
                      "ch02_funnel_aarrr"],
    "第 5 章 银行 KPI": ["ch05_kpi", "ch05_risk", "ch05_income",
                    "ch05_age", "ch05_cross", "ch05_purpose"],
    "第 8 章 SQL 实践": [f"ch08_q{i:02d}" for i in range(1, 11)],
    "第 9 章 用户画像": ["ch09_user_profile", "ch09_combo"],
    "第 10 章 效应分解": ["ch10_decompose", "ch10_seasonal", "ch10_forecast"],
}

CSS = """
:root { --ink:#1f2328; --muted:#6b7280; --line:#e5e7eb; --bg:#f7f8fa; --accent:#4472C4; }
* { box-sizing: border-box; }
body { margin:0; padding:32px 20px 64px; background:var(--bg); color:var(--ink);
       font-family:"Microsoft YaHei","PingFang SC","Segoe UI",sans-serif; }
.wrap { max-width:1080px; margin:0 auto; }
h1 { font-size:26px; margin:0 0 6px; }
.sub { color:var(--muted); font-size:13px; margin-bottom:26px; }
.card { background:#fff; border:1px solid var(--line); border-radius:10px;
        padding:18px 20px; margin-bottom:18px; }
.card h2 { font-size:15px; margin:0 0 10px; color:var(--accent); }
.badge { display:inline-block; font-size:12px; color:#fff; background:var(--accent);
         border-radius:4px; padding:1px 7px; margin-right:8px; }
.note { color:var(--muted); font-size:12.5px; margin:6px 0 0; }
img { width:100%; border:1px solid var(--line); border-radius:6px; margin-top:12px; }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
ul { margin:8px 0 0; padding-left:20px; font-size:13px; line-height:1.9; }
iframe { width:100%; height:820px; border:1px solid var(--line); border-radius:6px;
         margin-top:12px; background:#fff; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:8px; }
.grid div { font-size:13px; }
"""


def build() -> str:
    rows = []
    for fname, chapter, title, desc in FIGURES:
        if not os.path.exists(os.path.join(OUT, fname)):
            continue
        rows.append(
            f'<div class="card"><h2><span class="badge">{chapter}</span>{title}</h2>'
            f'<p class="note">{desc}</p>'
            f'<img src="{fname}" alt="{title}"></div>'
        )

    csv_html = []
    for group, names in CSV_GROUPS.items():
        items = []
        for name in names:
            if os.path.exists(os.path.join(OUT, f"{name}.csv")):
                items.append(f'<div><a href="{name}.csv">{name}.csv</a></div>')
        if items:
            csv_html.append(f'<div class="card"><h2>{group}（{len(items)} 个）</h2>'
                            f'<div class="grid">{"".join(items)}</div></div>')

    dash = ""
    if os.path.exists(os.path.join(OUT, "ch02_dashboard.html")):
        dash = ('<div class="card"><h2>交互看板（第 2 章，5 个图表）</h2>'
                '<p class="note">pyecharts 生成，可悬停查看数值；'
                '也可<a href="ch02_dashboard.html">在新标签页单独打开</a>。</p>'
                '<iframe src="ch02_dashboard.html"></iframe></div>')

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>教材实验 · 结果总览</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>《商业数据分析》教材实验 · 结果总览</h1>
<p class="sub">Excel / Power BI / MySQL 案例的 Python 复刻　·　
{len(rows)} 张静态图 + 1 个交互看板 + 结果 csv　·　生成于 {stamp}</p>
{''.join(rows)}
{dash}
{''.join(csv_html)}
<div class="card"><h2>怎么复现</h2>
<ul>
<li><code>py -3.13 run_all.py</code> —— 一键跑完全部章节</li>
<li><code>py -3.13 scripts/ch05_bank_kpi.py</code> —— 单独跑某一章</li>
<li>口径差异与 Excel/PBI → pandas 技术映射表见 <code>README.md</code></li>
</ul></div>
</div></body></html>
"""
    path = os.path.join(OUT, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path


if __name__ == "__main__":
    p = build()
    print(f"总览页 → {p}")
    n = len([f for f in FIGURES if os.path.exists(os.path.join(OUT, f[0]))])
    print(f"  收录 {n} 张图与全部结果 csv")
