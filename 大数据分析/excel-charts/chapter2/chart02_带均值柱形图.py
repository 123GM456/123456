import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华北", "华南", "东北", "西北", "西南", "华东"]
sales = [2354, 1902, 3524, 2698, 2896, 2563]
avg = round(sum(sales) / len(sales), 2)

bar = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis("销售量", sales, itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各区域销售量与均值对比", subtitle="数据来源：第二章示例2 带均值柱形图"),
        xaxis_opts=opts.AxisOpts(name="区域"),
        yaxis_opts=opts.AxisOpts(name="销售量"),
    )
)
line = (
    Line()
    .add_xaxis(regions)
    .add_yaxis("均值", [avg] * len(regions), is_smooth=True,
               linestyle_opts=opts.LineStyleOpts(color="#ED7D31", width=2, type_="dashed"),
               label_opts=opts.LabelOpts(color="#ED7D31", formatter=str(avg)))
)
bar.overlap(line)
bar.render(os.path.join(OUT, "chart02_带均值柱形图.html"))
print("已生成: output/chart02_带均值柱形图.html")
