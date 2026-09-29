import os
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月"]
rate = [0.536, 0.498, 0.527, 0.708, 0.609, 0.496, 0.586, 0.704]

c = (
    Line(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(months)
    .add_yaxis(
        "完成率",
        rate,
        is_smooth=True,
        symbol="diamond",
        symbol_size=12,
        label_opts=opts.LabelOpts(formatter=JsCode("function(p){return (p.value*100).toFixed(0)+'%';}")),
        linestyle_opts=opts.LineStyleOpts(color="#ED7D31", width=2),
        itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31", border_color="#FFFFFF", border_width=2),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="每月完成率走势（菱形标记）", subtitle="数据来源：第二章示例12 菱形走势图"),
        xaxis_opts=opts.AxisOpts(name="月份"),
        yaxis_opts=opts.AxisOpts(name="完成率", axislabel_opts=opts.LabelOpts(formatter="{value}")),
    )
)
c.render(os.path.join(OUT, "chart12_菱形走势图.html"))
print("已生成: output/chart12_菱形走势图.html")
