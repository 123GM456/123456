import os
from pyecharts import options as opts
from pyecharts.charts import Liquid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

rate = 0.65

c = (
    Liquid(init_opts=opts.InitOpts(width="600px", height="520px"))
    .add("", [rate], is_outline_show=True,
         color=["#2F6FB4"],
         label_opts=opts.LabelOpts(font_size=40, color="#2F6FB4",
                                   formatter="{c}%", position="inside"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="完成率水球图", subtitle="数据来源：第二章示例15 水球图"),
    )
)
c.render(os.path.join(OUT, "chart15_水球图.html"))
print("已生成: output/chart15_水球图.html")
