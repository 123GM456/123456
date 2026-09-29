import os
from pyecharts import options as opts
from pyecharts.charts import Liquid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

rate = 0.65

c = (
    Liquid(init_opts=opts.InitOpts(width="600px", height="520px"))
    .add("", [rate, rate], is_outline_show=False,
         shape="roundRect",
         color=["#2F6FB4", "#5B9BD5"],
         label_opts=opts.LabelOpts(font_size=40, color="#2F6FB4",
                                   formatter="{c}%", position="inside"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="波浪水球图", subtitle="数据来源：第二章示例16 波浪水球图"),
    )
)
c.render(os.path.join(OUT, "chart16_波浪水球图.html"))
print("已生成: output/chart16_波浪水球图.html")
