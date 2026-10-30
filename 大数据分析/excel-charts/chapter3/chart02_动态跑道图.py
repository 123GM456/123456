import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Timeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

depts = ["人力部", "行政部", "财务部", "工程部", "采购部", "销售部"]
months = ["1月", "2月", "3月", "4月"]
data = [
    [130, 226, 238, 293, 326, 451],
    [138, 206, 228, 305, 349, 456],
    [130, 217, 255, 314, 316, 406],
    [129, 226, 226, 264, 359, 433],
]

tl = Timeline(init_opts=opts.InitOpts(width="1000px", height="560px"))
for i, m in enumerate(months):
    nums = data[i]
    maxn = max(nums)
    bar = (
        Bar()
        .add_xaxis(depts)
        .add_yaxis(
            "人数",
            nums,
            bar_width=22,
            itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5", border_radius=[12, 12, 12, 12]),
            label_opts=opts.LabelOpts(position="right"),
        )
        .add_yaxis(
            "占位",
            [maxn - v for v in nums],
            bar_width=22,
            stack="bg",
            itemstyle_opts=opts.ItemStyleOpts(color="rgba(0,0,0,0)"),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .reversal_axis()
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{m}各部门人数（动态跑道图）", subtitle="数据来源：第三章示例2 动态跑道图"),
            xaxis_opts=opts.AxisOpts(name="人数"),
            yaxis_opts=opts.AxisOpts(name="部门"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    tl.add(bar, m)
tl.add_schema(is_auto_play=True, play_interval=1200)
tl.render(os.path.join(OUT, "ch3_02_动态跑道图.html"))
print("已生成: output/ch3_02_动态跑道图.html")
