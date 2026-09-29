import os
from pyecharts import options as opts
from pyecharts.charts import Pie, Timeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

sources = ["首页推荐", "关注页面", "搜索", "个人主页", "其他来源"]
periods = ["近7天", "近30天"]
data = [
    [0.44, 0.17, 0.15, 0.08, 0.16],
    [0.38, 0.21, 0.15, 0.09, 0.17],
]

tl = Timeline(init_opts=opts.InitOpts(width="1000px", height="560px"))
for i, p in enumerate(periods):
    pie = (
        Pie()
        .add(
            "",
            list(zip(sources, data[i])),
            radius=["35%", "75%"],
            center=["50%", "55%"],
            rosetype="radius",
            label_opts=opts.LabelOpts(formatter="{b}\n{d}%"),
            itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=2),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{p}流量来源（动态南丁格尔圆环图）", subtitle="数据来源：第三章示例3 动态南丁格尔圆环图"),
            legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
            tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"),
        )
    )
    tl.add(pie, p)
tl.add_schema(is_auto_play=True, play_interval=1500)
tl.render(os.path.join(OUT, "ch3_03_动态南丁格尔圆环图.html"))
print("已生成: output/ch3_03_动态南丁格尔圆环图.html")
