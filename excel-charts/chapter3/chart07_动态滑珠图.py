import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Scatter, Timeline
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华北", "华南", "东北", "西北", "西南", "华东"]
months = ["1月", "2月", "3月", "4月", "5月", "6月"]
data = [
    [0.32, 0.49, 0.65, 0.73, 0.536, 0.32],
    [0.45, 0.36, 0.53, 0.63, 0.498, 0.49],
    [0.66, 0.54, 0.58, 0.61, 0.527, 0.65],
    [0.52, 0.39, 0.48, 0.53, 0.708, 0.73],
    [0.69, 0.415, 0.445, 0.47, 0.7035, 0.536],
    [0.771, 0.403, 0.399, 0.408, 0.758, 0.7468],
]
n = len(regions)

tl = Timeline(init_opts=opts.InitOpts(width="1000px", height="560px"))
for i, m in enumerate(months):
    vals = data[i]
    bar = (
        Bar()
        .add_xaxis(regions)
        .add_yaxis("轨道", [1] * n, bar_width=16,
                   itemstyle_opts=opts.ItemStyleOpts(color="#E8EEF7"),
                   label_opts=opts.LabelOpts(is_show=False))
        .reversal_axis()
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{m}各区域完成率（动态滑珠图）", subtitle="数据来源：第三章示例7 动态滑珠图"),
            xaxis_opts=opts.AxisOpts(name="完成率", max_=1),
            yaxis_opts=opts.AxisOpts(name="区域"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    sc = (
        Scatter()
        .add_xaxis([])
        .add_yaxis("完成率", [[vals[j], j] for j in range(n)], symbol="circle", symbol_size=22,
                   label_opts=opts.LabelOpts(position="right", formatter=JsCode("function(p){return p.value[0];}")),
                   itemstyle_opts=opts.ItemStyleOpts(color="#2F6FB4", border_color="#fff", border_width=2))
    )
    bar.overlap(sc)
    tl.add(bar, m)
tl.add_schema(is_auto_play=True, play_interval=1200)
tl.render(os.path.join(OUT, "ch3_07_动态滑珠图.html"))
print("已生成: output/ch3_07_动态滑珠图.html")
