import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华东", "西北", "东北", "华北", "华南"]
p2022 = [0.36, 0.31, 0.18, 0.13, 0.09]
p2021 = [0.42, 0.26, 0.19, 0.12, 0.05]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("2022年占比", p2022,
               itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("2021年占比", [-v for v in p2021],
               itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"),
               label_opts=opts.LabelOpts(formatter="{c}"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="2022年 vs 2021年区域销量占比（蝴蝶图）", subtitle="数据来源：第二章示例7 蝴蝶图"),
        xaxis_opts=opts.AxisOpts(name="区域"),
        yaxis_opts=opts.AxisOpts(name="占比"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
c.render(os.path.join(OUT, "chart07_蝴蝶图.html"))
print("已生成: output/chart07_蝴蝶图.html")
