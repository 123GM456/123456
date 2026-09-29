import os
from pyecharts import options as opts
from pyecharts.charts import Pie

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

rate = 0.85

c = (
    Pie(init_opts=opts.InitOpts(width="600px", height="520px"))
    .add(
        "",
        [("完成", rate), ("未完成", 1 - rate)],
        radius=["55%", "75%"],
        label_opts=opts.LabelOpts(is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=2),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="任务完成率", subtitle="数据来源：第二章示例14 单值圆环图"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    .set_series_opts(
        tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"),
        label_opts=opts.LabelOpts(
            position="center",
            formatter="{d}%",
            font_size=36,
            font_weight="bold",
            color="#2F6FB4",
        ),
    )
)
c.render(os.path.join(OUT, "chart14_单值圆环图.html"))
print("已生成: output/chart14_单值圆环图.html")
