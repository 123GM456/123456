import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

items = ["口红", "面膜", "隔离", "粉底液"]
sales = [2800, 2564, 2282, 2353]
profit = [1896, 1563, 986, 1324]
rate = [0.677, 0.610, 0.432, 0.563]

bar = (
    Bar(init_opts=opts.InitOpts(width="1000px", height="560px"))
    .add_xaxis(items)
    .add_yaxis("销售额", sales, itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("利润", profit, itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各品类销售额与利润率（动态组合图）", subtitle="数据来源：第三章示例4 动态组合图"),
        xaxis_opts=opts.AxisOpts(name="品类"),
        yaxis_opts=opts.AxisOpts(name="金额"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
line = (
    Line()
    .add_xaxis(items)
    .add_yaxis(
        "利润率",
        rate,
        yaxis_index=1,
        is_smooth=True,
        label_opts=opts.LabelOpts(formatter="{c}%"),
        linestyle_opts=opts.LineStyleOpts(color="#70AD47", width=2),
        itemstyle_opts=opts.ItemStyleOpts(color="#70AD47"),
    )
)
bar.overlap(line)
bar.extend_axis(
    yaxis=opts.AxisOpts(
        name="利润率",
        type_="value",
        max_=1,
        axislabel_opts=opts.LabelOpts(formatter="{value}%"),
        splitline_opts=opts.SplitLineOpts(is_show=False),
    )
)
bar.render(os.path.join(OUT, "ch3_04_动态组合图.html"))
print("已生成: output/ch3_04_动态组合图.html")
