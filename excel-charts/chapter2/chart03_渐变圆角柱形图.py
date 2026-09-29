import os
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

items = ["口红", "面膜", "隔离", "防晒", "精华", "面霜"]
sales = [653, 523, 648, 856, 714, 785]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(items)
    .add_yaxis(
        "销量",
        sales,
        itemstyle_opts=opts.ItemStyleOpts(
            color=JsCode(
                "new echarts.graphic.LinearGradient(0,0,0,1,"
                "[{offset:0,color:'#8bc8ea'},{offset:1,color:'#2f6fb4'}])"
            ),
            border_radius=[8, 8, 0, 0],
        ),
        label_opts=opts.LabelOpts(position="top"),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="商品销量对比", subtitle="数据来源：第二章示例3 渐变圆角柱形图"),
        xaxis_opts=opts.AxisOpts(name="商品"),
        yaxis_opts=opts.AxisOpts(name="销量"),
    )
)
c.render(os.path.join(OUT, "chart03_渐变圆角柱形图.html"))
print("已生成: output/chart03_渐变圆角柱形图.html")
