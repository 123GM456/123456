import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Scatter
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华东", "西北", "东北", "华北", "华南"]
rate = [0.35, 0.51, 0.62, 0.74, 0.86]
n = len(regions)

bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("轨道", [1] * n, bar_width=16,
               itemstyle_opts=opts.ItemStyleOpts(color="#E8EEF7"),
               label_opts=opts.LabelOpts(is_show=False))
    .reversal_axis()
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各区域完成率（滑珠图）", subtitle="数据来源：第二章示例29 滑珠图"),
        xaxis_opts=opts.AxisOpts(name="完成率", max_=1),
        yaxis_opts=opts.AxisOpts(name="区域"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
)
sc = (
    Scatter()
    .add_xaxis([])
    .add_yaxis("完成率", [[rate[i], i] for i in range(n)], symbol="circle", symbol_size=22,
               label_opts=opts.LabelOpts(position="right", formatter=JsCode("function(p){return p.value[0];}")),
               itemstyle_opts=opts.ItemStyleOpts(color="#2F6FB4", border_color="#fff", border_width=2))
)
bar.overlap(sc)
bar.render(os.path.join(OUT, "chart29_滑珠图.html"))
print("已生成: output/chart29_滑珠图.html")
