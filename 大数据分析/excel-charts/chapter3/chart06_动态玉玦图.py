import os
from pyecharts import options as opts
from pyecharts.charts import Pie, Timeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

sources = ["个人主页", "搜索", "关注页面", "首页推荐"]
periods = ["近7天", "近30天"]
data = [
    [0.13, 0.19, 0.32, 0.36],
    [0.09, 0.24, 0.29, 0.38],
]

tl = Timeline(init_opts=opts.InitOpts(width="1000px", height="560px"))
for i, p in enumerate(periods):
    pie = (
        Pie()
        .add(
            "",
            list(zip(sources, data[i])),
            radius=["40%", "75%"],
            center=["50%", "55%"],
            start_angle=90,
            min_angle=90,
            label_opts=opts.LabelOpts(formatter="{b}\n{d}%"),
            itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=2),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{p}流量来源（VBA动态玉玦图）", subtitle="数据来源：第三章示例6 VBA动态玉玦图"),
            legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
            tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"),
        )
    )
    tl.add(pie, p)
tl.add_schema(is_auto_play=True, play_interval=1500)
tl.render(os.path.join(OUT, "ch3_06_动态玉玦图.html"))
print("已生成: output/ch3_06_动态玉玦图.html")
