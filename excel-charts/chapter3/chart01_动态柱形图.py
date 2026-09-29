import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Timeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华北", "华南", "东北", "西北", "西南", "华东"]
months = ["1月", "2月", "3月", "4月", "5月", "6月"]
data = [
    [259, 247, 705, 513, 463, 384],
    [235, 266, 529, 324, 579, 282],
    [330, 342, 705, 540, 492, 308],
    [282, 342, 599, 270, 492, 384],
    [282, 323, 705, 486, 405, 308],
    [965, 380, 282, 567, 463, 897],
]

tl = Timeline(init_opts=opts.InitOpts(width="1000px", height="560px"))
for i, m in enumerate(months):
    bar = (
        Bar()
        .add_xaxis(regions)
        .add_yaxis("销量", data[i], itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{m}各区域销量（动态柱形图）", subtitle="数据来源：第三章示例1 动态柱形图"),
            xaxis_opts=opts.AxisOpts(name="区域"),
            yaxis_opts=opts.AxisOpts(name="销量"),
        )
    )
    tl.add(bar, m)
tl.add_schema(is_auto_play=True, play_interval=1200)
tl.render(os.path.join(OUT, "ch3_01_动态柱形图.html"))
print("已生成: output/ch3_01_动态柱形图.html")
