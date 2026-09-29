import os
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

items = ["口红", "面膜", "隔离", "防晒", "精华", "面霜", "眼影", "气垫"]
sales = [9221, 5102, 6571, 5760, 6321, 8612, 2645, 5321]
best = max(sales)

colors = JsCode(
    "function(p){return p.value === " + str(best) + " ? '#C00000' : '#5B9BD5';}"
)

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(items)
    .add_yaxis(
        "销量",
        sales,
        itemstyle_opts=opts.ItemStyleOpts(color=colors),
        label_opts=opts.LabelOpts(position="top"),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各商品销量（突出最高值）", subtitle="数据来源：第二章示例4 标注柱形图"),
        xaxis_opts=opts.AxisOpts(name="商品"),
        yaxis_opts=opts.AxisOpts(name="销量"),
    )
)
c.render(os.path.join(OUT, "chart04_标注柱形图.html"))
print("已生成: output/chart04_标注柱形图.html")
