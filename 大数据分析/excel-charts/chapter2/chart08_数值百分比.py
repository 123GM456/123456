import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华北", "华南", "东北", "西北", "西南", "华东"]
sales = [4321, 1946, 1536, 1872, 1369, 2109]
growth = [-0.136, -0.208, -0.093, -0.159, -0.179, -0.058]

bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("销量", sales, itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各区域销量与同比（数值百分比）", subtitle="数据来源：第二章示例8 数值百分比"),
        xaxis_opts=opts.AxisOpts(name="区域"),
        yaxis_opts=opts.AxisOpts(name="销量"),
    )
)
line = (
    Line()
    .add_xaxis(regions)
    .add_yaxis(
        "同比",
        growth,
        yaxis_index=1,
        is_smooth=True,
        label_opts=opts.LabelOpts(formatter="{c}%"),
        linestyle_opts=opts.LineStyleOpts(color="#ED7D31", width=2),
        itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"),
    )
)
bar.overlap(line)
bar.extend_axis(
    yaxis=opts.AxisOpts(
        name="同比",
        type_="value",
        axislabel_opts=opts.LabelOpts(formatter="{value}%"),
        splitline_opts=opts.SplitLineOpts(is_show=False),
    )
)
bar.render(os.path.join(OUT, "chart08_数值百分比.html"))
print("已生成: output/chart08_数值百分比.html")
