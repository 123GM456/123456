import os
from pyecharts import options as opts
from pyecharts.charts import Pie

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

ages = [("[20,30)", 0.375), ("[30,40)", 0.2917), ("[40,50)", 0.2083), (">=50", 0.125)]

c = (
    Pie(init_opts=opts.InitOpts(width="800px", height="520px"))
    .add(
        "",
        ages,
        radius=["15%", "75%"],
        center=["50%", "55%"],
        rosetype="radius",
        label_opts=opts.LabelOpts(formatter="{b}\n{d}%"),
        itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=2),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="年龄结构（南丁格尔圆环图）", subtitle="数据来源：第二章示例20 南丁格尔圆环图"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
        tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"),
    )
)
c.render(os.path.join(OUT, "chart20_南丁格尔圆环图.html"))
print("已生成: output/chart20_南丁格尔圆环图.html")
