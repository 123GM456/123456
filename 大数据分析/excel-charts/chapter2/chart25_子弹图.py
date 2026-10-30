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
    .add_yaxis("实际", actual, stack="b", bar_width=18,
               itemstyle_opts=opts.ItemStyleOpts(color="#2F6FB4"))
    .add_yaxis("目标", [t - a for a, t in zip(actual, target)], stack="b", bar_width=18,
               itemstyle_opts=opts.ItemStyleOpts(color="rgba(0,0,0,0)"),
               label_opts=opts.LabelOpts(is_show=False))
    .reversal_axis()
    .set_global_opts(
        title_opts=opts.TitleOpts(title="实际完成 vs 目标（子弹图）", subtitle="数据来源：第二章示例25 子弹图"),
        xaxis_opts=opts.AxisOpts(name="销量"),
        yaxis_opts=opts.AxisOpts(name="商品"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
)
c.render(os.path.join(OUT, "chart25_子弹图.html"))
print("已生成: output/chart25_子弹图.html")
