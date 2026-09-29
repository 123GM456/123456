import os
from pyecharts import options as opts
from pyecharts.charts import Line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

months = ["2021/5", "2021/6", "2021/7", "2021/8", "2021/9", "2021/10",
          "2021/11", "2021/12", "2022/1", "2022/2", "2022/3"]
sales = [146, 198, 296, 412, 506, 615, 789, 1021, 3782, 3215, 2936]

c = (
    Line(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(months)
    .add_yaxis(
        "销量",
        sales,
        is_smooth=True,
        is_symbol_show=False,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(color="#2F6FB4", width=3),
        areastyle_opts=opts.AreaStyleOpts(opacity=0.15, color="#5B9BD5"),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="销量平滑趋势", subtitle="数据来源：第二章示例11 平滑折线图"),
        xaxis_opts=opts.AxisOpts(name="月份"),
        yaxis_opts=opts.AxisOpts(name="销量"),
    )
)
c.render(os.path.join(OUT, "chart11_平滑折线图.html"))
print("已生成: output/chart11_平滑折线图.html")
