import os
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

regions = ["华北", "华南", "东北", "西北", "西南", "华东"]
sales = [2354, 1902, 3524, 2698, 2896, 2563]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(regions)
    .add_yaxis(
        "销售量",
        sales,
        itemstyle_opts=opts.ItemStyleOpts(
            color=JsCode(
                "new echarts.graphic.LinearGradient(0,0,0,1,"
                "[{offset:0,color:'#8bc8ea'},{offset:1,color:'#2f6fb4'}])"
            )
        ),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各区域销售量", subtitle="数据来源：第二章示例1 渐变柱形图"),
        xaxis_opts=opts.AxisOpts(name="区域"),
        yaxis_opts=opts.AxisOpts(name="销售量"),
    )
)
c.render(os.path.join(OUT, "chart01_渐变柱形图.html"))
print("已生成: output/chart01_渐变柱形图.html")
