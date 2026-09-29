import os
from pyecharts import options as opts
from pyecharts.charts import Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

months = ["1月", "2月", "3月", "4月", "5月", "6月"]
s2021 = [1686, 1345, 1934, 1658, 1865, 1936]
s2022 = [1385, 1846, 1654, 1936, 2564, 2236]

c = (
    Line(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(months)
    .add_yaxis("2021年", s2021, is_smooth=True, is_symbol_show=False,
               linestyle_opts=opts.LineStyleOpts(color="#5B9BD5", width=2))
    .add_yaxis("2022年", s2022, is_smooth=True, is_symbol_show=False,
               linestyle_opts=opts.LineStyleOpts(color="#ED7D31", width=2))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="2021年 vs 2022年销量对比", subtitle="数据来源：第二章示例13 对比折线图"),
        xaxis_opts=opts.AxisOpts(name="月份"),
        yaxis_opts=opts.AxisOpts(name="销量"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
c.render(os.path.join(OUT, "chart13_对比折线图.html"))
print("已生成: output/chart13_对比折线图.html")
