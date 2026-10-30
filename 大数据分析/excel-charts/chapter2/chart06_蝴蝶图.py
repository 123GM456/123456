import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华东", "西北", "东北", "华北", "华南"]
sales2022 = [1215, 1321, 1426, 1531, 2238]
sales2021 = [1003, 1265, 1531, 1436, 2066]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("2022年销量", sales2022,
               itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("2021年销量", [-v for v in sales2021],
               itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"),
               label_opts=opts.LabelOpts(formatter="{c}"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="2022年 vs 2021年区域销量（蝴蝶图）", subtitle="数据来源：第二章示例6 蝴蝶图"),
        xaxis_opts=opts.AxisOpts(name="区域"),
        yaxis_opts=opts.AxisOpts(name="销量"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
c.render(os.path.join(OUT, "chart06_蝴蝶图.html"))
print("已生成: output/chart06_蝴蝶图.html")
