import os
from pyecharts import options as opts
from pyecharts.charts import Pie

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

ages = [(">=50", 0.125), ("[40,50)", 0.2083), ("[30,40)", 0.2917), ("[20,30)", 0.375)]
values = [v for _, v in ages]

c = (
    Pie(init_opts=opts.InitOpts(width="700px", height="520px"))
    .add(
        "",
        ages,
        radius=["40%", "75%"],
        start_angle=90,
        min_angle=90,
        label_opts=opts.LabelOpts(formatter="{b}\n{d}%"),
        itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=2),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="年龄结构玉玦图", subtitle="数据来源：第二章示例17 玉玦图"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
        tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"),
    )
)
c.render(os.path.join(OUT, "chart17_玉玦图.html"))
print("已生成: output/chart17_玉玦图.html")
