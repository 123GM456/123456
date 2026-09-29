import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

depts = ["人力部", "行政部", "财务部", "工程部", "采购部", "销售部"]
nums = [130, 226, 238, 293, 326, 451]
maxn = max(nums)

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(depts)
    .add_yaxis(
        "人数",
        nums,
        bar_width=24,
        itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5", border_radius=[12, 12, 12, 12]),
        label_opts=opts.LabelOpts(position="right"),
    )
    .add_yaxis(
        "占位",
        [maxn - v for v in nums],
        bar_width=24,
        stack="bg",
        itemstyle_opts=opts.ItemStyleOpts(color="rgba(0,0,0,0)"),
        label_opts=opts.LabelOpts(is_show=False),
    )
    .reversal_axis()
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各部门人数（跑道图）", subtitle="数据来源：第二章示例18 跑道图"),
        xaxis_opts=opts.AxisOpts(name="人数", splitline_opts=opts.SplitLineOpts(is_show=True)),
        yaxis_opts=opts.AxisOpts(name="部门"),
        legend_opts=opts.LegendOpts(is_show=False),
    )
)
c.render(os.path.join(OUT, "chart18_跑道图.html"))
print("已生成: output/chart18_跑道图.html")
