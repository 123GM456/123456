import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华北", "华南", "东北", "西北", "西南", "华东"]
s2022 = [2354, 1902, 3524, 2698, 2896, 2563]
s2021 = [2021, 1563, 3213, 2531, 2631, 2361]
growth = [0.16, 0.22, 0.10, 0.07, 0.10, 0.09]

bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("2022年", s2022, itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("2021年", s2021, itemstyle_opts=opts.ItemStyleOpts(color="#A9CBE8"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="区域销量年度对比与同比", subtitle="数据来源：第二章示例27 簇状柱形折线图"),
        xaxis_opts=opts.AxisOpts(name="区域"),
        yaxis_opts=opts.AxisOpts(name="销量"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
line = (
    Line()
    .add_xaxis(regions)
    .add_yaxis(
        "同比",
        growth,
        yaxis_index=1,
        is_smooth=True,
        label_opts=opts.LabelOpts(formatter="{c}%"),
        linestyle_opts=opts.LineStyleOpts(color="#ED7D31", width=2),
        itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"),
    )
)
bar.overlap(line)
bar.extend_axis(
    yaxis=opts.AxisOpts(
        name="同比",
        type_="value",
        axislabel_opts=opts.LabelOpts(formatter="{value}%"),
        splitline_opts=opts.SplitLineOpts(is_show=False),
    )
)
bar.render(os.path.join(OUT, "chart27_簇状柱形折线图.html"))
print("已生成: output/chart27_簇状柱形折线图.html")
