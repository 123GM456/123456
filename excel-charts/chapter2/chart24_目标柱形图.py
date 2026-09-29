import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

items = ["口红", "面膜", "隔离", "防晒", "精华", "面霜"]
actual = [653, 523, 648, 856, 714, 785]
target = [700, 500, 600, 900, 600, 600]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(items)
    .add_yaxis("实际销量", actual, itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("目标销量", target, itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="实际销量 vs 目标销量", subtitle="数据来源：第二章示例24 目标柱形图"),
        xaxis_opts=opts.AxisOpts(name="商品"),
        yaxis_opts=opts.AxisOpts(name="销量"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
c.render(os.path.join(OUT, "chart24_目标柱形图.html"))
print("已生成: output/chart24_目标柱形图.html")
