import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

edus = ["高中", "专科", "本科", "硕士", "博士"]
income = [5853.6, 6908.0, 6138.3, 6739.0, 7187.0]
avg = round(sum(income) / len(income), 1)

c = (
    Bar(init_opts=opts.InitOpts(width="1000px", height="560px"))
    .add_xaxis(edus)
    .add_yaxis(
        "平均月收入",
        income,
        itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5", border_radius=[8, 8, 0, 0]),
        label_opts=opts.LabelOpts(position="top", formatter="{c}"),
        markline_opts=opts.MarkLineOpts(
            data=[opts.MarkLineItem(y=avg, name="总平均")],
            linestyle_opts=opts.LineStyleOpts(color="#ED7D31", type_="dashed"),
            label_opts=opts.LabelOpts(position="end", formatter=f"总平均 {avg}"),
        ),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="各学历平均月收入（透视表切片器）", subtitle="数据来源：第三章示例5 透视表切片器"),
        xaxis_opts=opts.AxisOpts(name="学历"),
        yaxis_opts=opts.AxisOpts(name="月收入"),
    )
)
c.render(os.path.join(OUT, "ch3_05_透视表切片器.html"))
print("已生成: output/ch3_05_透视表切片器.html")
