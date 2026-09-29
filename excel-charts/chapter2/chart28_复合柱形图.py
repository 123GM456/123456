import os
from pyecharts import options as opts
from pyecharts.charts import Bar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
monthly = [2354, 1902, 3524, 2698, 2896, 2563, 3156, 2896, 3621, 2635, 2963, 2789]
quarterly = [7780, 7780, 7780, 8157, 8157, 8157, 9673, 9673, 9673, 8387, 8387, 8387]

c = (
    Bar(init_opts=opts.InitOpts(width="900px", height="520px"))
    .add_xaxis(months)
    .add_yaxis("月度销量", monthly, bar_width=14,
               itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5"))
    .add_yaxis("季度销量", quarterly, bar_width=28,
               itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="月度销量与季度销量对比", subtitle="数据来源：第二章示例28 复合柱形图"),
        xaxis_opts=opts.AxisOpts(name="月份"),
        yaxis_opts=opts.AxisOpts(name="销量"),
        legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
    )
)
c.render(os.path.join(OUT, "chart28_复合柱形图.html"))
print("已生成: output/chart28_复合柱形图.html")
