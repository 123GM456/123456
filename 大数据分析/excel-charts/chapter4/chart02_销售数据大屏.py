import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Line, Page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)


def wan(v):
    return round(v / 10000, 1)


months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
sales_m = [1452246, 1186299, 1312695, 1242605, 1165084, 1081054,
           1216160, 1117427, 1342887, 1372817, 1195537, 1468738]

trend = Line()
trend.add_xaxis(months)
trend.add_yaxis("销售额(万)", [wan(v) for v in sales_m], is_smooth=True, is_symbol_show=False,
                areastyle_opts=opts.AreaStyleOpts(opacity=0.15),
                linestyle_opts=opts.LineStyleOpts(color="#2F6FB4", width=3),
                label_opts=opts.LabelOpts(is_show=False))
trend.set_global_opts(title_opts=opts.TitleOpts(title="月度销售额趋势"),
                      xaxis_opts=opts.AxisOpts(name="月份"),
                      yaxis_opts=opts.AxisOpts(name="万元"))

regions = ["华南", "华北", "华东", "东北", "西北", "西南"]
sales_r = [5607324, 3071869, 2751513, 2061871, 1169781, 491192]
reg = Bar()
reg.add_xaxis(regions)
reg.add_yaxis("销售额(万)", [wan(v) for v in sales_r],
              itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5", border_radius=[6, 6, 0, 0]),
              label_opts=opts.LabelOpts(position="top"))
reg.set_global_opts(title_opts=opts.TitleOpts(title="区域销售额"),
                    xaxis_opts=opts.AxisOpts(name="区域"),
                    yaxis_opts=opts.AxisOpts(name="万元"))

cat = Pie()
cat.add("", [("数码电子", 6053895), ("家具产品", 5282409), ("办公用品", 3817246)],
        radius=["40%", "70%"], center=["50%", "55%"],
        label_opts=opts.LabelOpts(formatter="{b}\n{d}%"))
cat.set_global_opts(title_opts=opts.TitleOpts(title="产品类别占比"),
                    legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
                    tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"))

ships = ["顺丰", "圆通", "申通", "韵达", "中通", "EMS"]
sales_s = [6636163, 4073359, 1649397, 1417956, 1061701, 314973]
ship = Bar()
ship.add_xaxis(ships)
ship.add_yaxis("销售额(万)", [wan(v) for v in sales_s],
               itemstyle_opts=opts.ItemStyleOpts(color="#70AD47", border_radius=[0, 6, 6, 0]),
               label_opts=opts.LabelOpts(position="right"))
ship.reversal_axis()
ship.set_global_opts(title_opts=opts.TitleOpts(title="快递公司销售额"),
                     xaxis_opts=opts.AxisOpts(name="万元"),
                     yaxis_opts=opts.AxisOpts(name="快递公司"))

cost = Pie()
cost.add("", [("推广", 405.8), ("人工", 214.7), ("其他", 208.4), ("产品", 100.4)],
         radius=["40%", "70%"], center=["50%", "55%"],
         label_opts=opts.LabelOpts(formatter="{b}\n{d}%"))
cost.set_global_opts(title_opts=opts.TitleOpts(title="成本构成"),
                     legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
                     tooltip_opts=opts.TooltipOpts(formatter="{b}: {d}%"))

top = [("KI Conference Tables", 16.98), ("Xerox 193", 16.81), ("Phone 918", 15.35),
       ("Canon PC940 Copier", 11.98), ("3M Organizer Strips", 10.27), ("Crate-A-Files", 7.78),
       ("Document Clip Frames", 6.69), ("TDK 4.7GB DVD-R", 6.64)]
rank = Bar()
rank.add_xaxis([t[0] for t in top][::-1])
rank.add_yaxis("销售额(万)", [t[1] for t in top][::-1],
               itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31", border_radius=[0, 6, 6, 0]),
               label_opts=opts.LabelOpts(position="right"))
rank.reversal_axis()
rank.set_global_opts(title_opts=opts.TitleOpts(title="销售额TOP8产品"),
                     xaxis_opts=opts.AxisOpts(name="万元"),
                     yaxis_opts=opts.AxisOpts(name="产品"))

page = Page(layout=Page.SimplePageLayout)
page.add(trend, reg, cat, ship, cost, rank)
page.render(os.path.join(OUT, "ch4_02_销售数据大屏.html"))
print("已生成: output/ch4_02_销售数据大屏.html")
