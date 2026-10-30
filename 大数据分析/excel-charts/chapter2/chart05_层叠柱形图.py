import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

quarters = ["2021Q1", "2021Q2", "2021Q3", "2021Q4", "2022Q1", "2022Q2"]
sales = [3121, 4086, 4321, 4601, 4936, 4231]
profit = [1020, 1421, 1502, 1623, 1781, 1432]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(quarters)
    .add_yaxis("销售额", sales, stack="total", itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("利润额", profit, stack="total", itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各季度销售额与利润额", subtitle="数据来源：第二章示例5 层叠柱形图",
                                  pos_left="center", pos_top="1%"),
        xaxis_opts=opts.AxisOpts(name="季度"),
        yaxis_opts=opts.AxisOpts(name="金额"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
c.render(os.path.join(OUT, "chart05_层叠柱形图.html"))
print("已生成: output/chart05_层叠柱形图.html")
