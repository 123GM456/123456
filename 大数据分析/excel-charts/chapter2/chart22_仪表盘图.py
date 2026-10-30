import os
from pyecharts import options as opts
from pyecharts.charts import Gauge

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

c = (
    Gauge(init_opts=opts.InitOpts(width="700px", height="520px"))
    .add(
        "",
        [("完成度", 76)],
        min_=50,
        max_=150,
        split_number=10,
        radius="90%",
        start_angle=210,
        end_angle=-30,
        progress=opts.GaugeProgressOpts(
            is_show=True,
            width=18,
            itemstyle_opts=opts.ItemStyleOpts(color="#2F6FB4"),
        ),
        axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(width=18)),
        detail_label_opts=opts.GaugeDetailOpts(
            formatter="{value}", font_size=32, color="#2F6FB4", offset_center=[0, "50%"]
        ),
        title_label_opts=opts.GaugeTitleOpts(font_size=14),
        pointer=opts.GaugePointerOpts(width=6, itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31")),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="仪表盘图", subtitle="数据来源：第二章示例22 仪表盘图"),
    )
)
c.render(os.path.join(OUT, "chart22_仪表盘图.html"))
print("已生成: output/chart22_仪表盘图.html")
