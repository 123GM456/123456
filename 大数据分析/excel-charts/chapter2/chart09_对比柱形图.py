import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

items = ["口红", "面膜", "隔离", "防晒", "精华"]
s2021 = [3568, 4135, 4436, 4106, 4936]
s2022 = [2569, 3241, 2965, 3209, 3541]
diff = [a - b for a, b in zip(s2021, s2022)]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(items)
    .add_yaxis("2021年销量", s2021, itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("2022年销量", s2022, itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"))
    .add_yaxis("差值", diff, itemstyle_opts=opts.ItemStyleOpts(color="#A5A5A5"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="商品销量年度对比", subtitle="数据来源：第二章示例9 对比柱形图"),
        xaxis_opts=opts.AxisOpts(name="商品"),
        yaxis_opts=opts.AxisOpts(name="销量"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
c.render(os.path.join(OUT, "chart09_对比柱形图.html"))
print("已生成: output/chart09_对比柱形图.html")
