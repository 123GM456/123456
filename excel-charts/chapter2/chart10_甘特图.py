import os
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

tasks = [
    ("制定计划", 44621, 11, 0.51),
    ("方案设计", 44633, 8, 0.32),
    ("资源调配", 44642, 10, 0.21),
    ("第一阶段", 44653, 13, 0.85),
    ("第二阶段", 44667, 24, 0.36),
    ("第三阶段", 44692, 14, 0.68),
    ("项目总结", 44707, 7, 0.68),
]
names = [t[0] for t in tasks]
starts = [t[1] for t in tasks]
done = [round(t[2] * t[3], 2) for t in tasks]
remain = [round(t[2] * (1 - t[3]), 2) for t in tasks]
min_start = min(starts)
max_end = max(t[1] + t[2] for t in tasks)

fmt = JsCode("function(v){var d=new Date((v-25569)*86400000);return (d.getMonth()+1)+'月';}")

c = (
    Bar(init_opts=opts.InitOpts(width="1000px", height="520px"))
    .add_xaxis(names)
    .add_yaxis("占位", starts, stack="g", itemstyle_opts=opts.ItemStyleOpts(color="rgba(0,0,0,0)"),
               label_opts=opts.LabelOpts(is_show=False))
    .add_yaxis("已完成", done, stack="g", itemstyle_opts=opts.ItemStyleOpts(color="#2F6FB4"),
               label_opts=opts.LabelOpts(formatter="{c}天", color="#2F6FB4", position="right"))
    .add_yaxis("剩余", remain, stack="g", itemstyle_opts=opts.ItemStyleOpts(color="#A9CBE8"),
               label_opts=opts.LabelOpts(is_show=False))
    .reversal_axis()
    .set_global_opts(
        title_opts=opts.TitleOpts(title="项目进度甘特图", subtitle="数据来源：第二章示例10 甘特图"),
        xaxis_opts=opts.AxisOpts(name="时间", min_=min_start - 15, max_=max_end + 15,
                                 axislabel_opts=opts.LabelOpts(formatter=fmt)),
        yaxis_opts=opts.AxisOpts(name="任务", is_inverse=True),
        legend_opts=opts.LegendOpts(is_show=False),
        tooltip_opts=opts.TooltipOpts(trigger="item"),
    )
)
c.render(os.path.join(OUT, "chart10_甘特图.html"))
print("已生成: output/chart10_甘特图.html")
