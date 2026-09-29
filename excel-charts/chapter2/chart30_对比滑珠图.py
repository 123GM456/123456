import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Scatter
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华东", "西北", "东北", "华北", "华南"]
r2022 = [0.35, 0.51, 0.62, 0.74, 0.86]
r2021 = [0.45, 0.39, 0.53, 0.69, 0.92]
n = len(regions)

bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("轨道", [1] * n, bar_width=16,
               itemstyle_opts=opts.ItemStyleOpts(color="#E8EEF7"),
               label_opts=opts.LabelOpts(is_show=False))
    .reversal_axis()
    .set_global_opts(
        title_opts=opts.TitleOpts(title="2022 vs 2021 完成率（对比滑珠图）", subtitle="数据来源：第二章示例30 对比滑珠图"),
        xaxis_opts=opts.AxisOpts(name="完成率", max_=1),
        yaxis_opts=opts.AxisOpts(name="区域"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
)
sc22 = (
    Scatter()
    .add_xaxis([])
    .add_yaxis("2022", [[r2022[i], i] for i in range(n)], symbol="circle", symbol_size=18,
               label_opts=opts.LabelOpts(position="right", formatter=JsCode("function(p){return p.value[0];}")),
               itemstyle_opts=opts.ItemStyleOpts(color="#2F6FB4", border_color="#fff", border_width=2))
)
sc21 = (
    Scatter()
    .add_xaxis([])
    .add_yaxis("2021", [[r2021[i], i] for i in range(n)], symbol="circle", symbol_size=18,
               label_opts=opts.LabelOpts(position="left", formatter=JsCode("function(p){return p.value[0];}")),
               itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31", border_color="#fff", border_width=2))
)
bar.overlap(sc22)
bar.overlap(sc21)
bar.render(os.path.join(OUT, "chart30_对比滑珠图.html"))
print("已生成: output/chart30_对比滑珠图.html")
