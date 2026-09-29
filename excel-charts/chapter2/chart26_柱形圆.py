import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Scatter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华北", "华南", "东北", "西北", "西南", "华东"]
sales = [2354, 1902, 3524, 2698, 2896, 2563]
growth = [0.12, 0.25, 0.16, 0.21, 0.18, 0.25]

bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("销量", sales, bar_width=36,
               itemstyle_opts=opts.ItemStyleOpts(color="#A9CBE8", border_radius=[18, 18, 18, 18]))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各区域销量与同比（柱形圆）", subtitle="数据来源：第二章示例26 柱形圆"),
        xaxis_opts=opts.AxisOpts(name="区域"),
        yaxis_opts=opts.AxisOpts(name="销量"),
    )
)
sc = (
    Scatter()
    .add_xaxis(regions)
    .add_yaxis(
        "同比",
        [round(v * sales[i], 1) for i, v in enumerate(growth)],
        symbol="circle",
        symbol_size=10,
        label_opts=opts.LabelOpts(position="top", formatter="{c}"),
        itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"),
    )
)
bar.overlap(sc)
bar.render(os.path.join(OUT, "chart26_柱形圆.html"))
print("已生成: output/chart26_柱形圆.html")
