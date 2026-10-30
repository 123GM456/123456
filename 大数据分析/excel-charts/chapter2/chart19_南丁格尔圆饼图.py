import os
from pyecharts import options as opts
from pyecharts.charts import Pie

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

depts = [("销售部", 0.292), ("采购部", 0.227), ("工程部", 0.175),
         ("财务部", 0.136), ("行政部", 0.103), ("人力部", 0.067)]

c = (
    Pie(init_opts=opts.InitOpts(width="800px", height="520px"))
    .add(
        "",
        depts,
        radius=["15%", "75%"],
        center=["50%", "55%"],
        rosetype="radius",
        label_opts=opts.LabelOpts(formatter="{b}\n{d}%"),
        itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=2),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各部门人数占比（南丁格尔玫瑰图）", subtitle="数据来源：第二章示例19 南丁格尔圆饼图"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
        tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"),
    )
)
c.render(os.path.join(OUT, "chart19_南丁格尔圆饼图.html"))
print("已生成: output/chart19_南丁格尔圆饼图.html")
