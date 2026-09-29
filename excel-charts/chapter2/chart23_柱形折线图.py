import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

years = ["2017", "2018", "2019", "2020", "2021", "2022"]
sales = [1603, 2106, 2406, 3265, 3721, 3921]
growth = [0.27, 0.314, 0.142, 0.357, 0.140, 0.054]

bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(years)
    .add_yaxis("销售量", sales, itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="历年销售量与同比增长", subtitle="数据来源：第二章示例23 柱形折线图"),
        xaxis_opts=opts.AxisOpts(name="年份"),
        yaxis_opts=opts.AxisOpts(name="销售量"),
    )
)
line = (
    Line()
    .add_xaxis(years)
    .add_yaxis(
        "同比增长率",
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
        name="增长率",
        type_="value",
        axislabel_opts=opts.LabelOpts(formatter="{value}%"),
        splitline_opts=opts.SplitLineOpts(is_show=False),
    )
)
bar.render(os.path.join(OUT, "chart23_柱形折线图.html"))
print("已生成: output/chart23_柱形折线图.html")
