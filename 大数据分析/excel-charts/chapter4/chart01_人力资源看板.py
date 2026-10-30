import os
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

sex = Pie()
sex.add("", [("男", 882), ("女", 588)], radius=["45%", "70%"], center=["50%", "55%"],
        label_opts=opts.LabelOpts(formatter="{b} {c}人\n{d}%"))
sex.set_global_opts(title_opts=opts.TitleOpts(title="性别分布"),
                    legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
                    tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}人 ({d}%)"))

mar = Pie()
mar.add("", [("已婚", 673), ("单身", 470), ("离异", 327)], radius=["45%", "70%"], center=["50%", "55%"],
        label_opts=opts.LabelOpts(formatter="{b} {c}人\n{d}%"))
mar.set_global_opts(title_opts=opts.TitleOpts(title="婚姻状况"),
                    legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
                    tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}人 ({d}%)"))

edu = Bar()
edu.add_xaxis(["本科", "硕士研究生", "专科", "专科以下", "博士研究生"])
edu.add_yaxis("人数", [572, 398, 282, 170, 48],
              itemstyle_opts=opts.ItemStyleOpts(color="#5B9BD5", border_radius=[6, 6, 0, 0]),
              label_opts=opts.LabelOpts(position="top"))
edu.set_global_opts(title_opts=opts.TitleOpts(title="学历分布"),
                    xaxis_opts=opts.AxisOpts(name="学历"),
                    yaxis_opts=opts.AxisOpts(name="人数"))

dept = Bar()
dept.add_xaxis(["研发部", "销售部", "信息技术部", "人力资源部", "财务部", "行政部"])
dept.add_yaxis("人数", [799, 437, 162, 46, 17, 9],
               itemstyle_opts=opts.ItemStyleOpts(color="#ED7D31", border_radius=[6, 6, 0, 0]),
               label_opts=opts.LabelOpts(position="top"))
dept.set_global_opts(title_opts=opts.TitleOpts(title="部门人数"),
                     xaxis_opts=opts.AxisOpts(name="部门"),
                     yaxis_opts=opts.AxisOpts(name="人数"))

age = Bar()
age.add_xaxis(["40岁及以上", "30-34岁", "35-39岁", "25-29岁", "18-24岁"])
age.add_yaxis("人数", [522, 325, 297, 229, 97],
              itemstyle_opts=opts.ItemStyleOpts(color="#70AD47", border_radius=[6, 6, 0, 0]),
              label_opts=opts.LabelOpts(position="top"))
age.set_global_opts(title_opts=opts.TitleOpts(title="年龄结构"),
                    xaxis_opts=opts.AxisOpts(name="年龄段"),
                    yaxis_opts=opts.AxisOpts(name="人数"))

move = Pie()
move.add("", [("入职", 40), ("转入", 5), ("转出", 5), ("无变动", 1420)],
         radius=["40%", "70%"], center=["50%", "55%"],
         label_opts=opts.LabelOpts(formatter="{b} {c}人\n{d}%"))
move.set_global_opts(title_opts=opts.TitleOpts(title="本月入转调"),
                     legend_opts=opts.LegendOpts(pos_bottom="0%", pos_left="center", orient="horizontal"),
                     tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}人 ({d}%)"))

page = Page(layout=Page.SimplePageLayout)
page.add(sex, mar, edu, dept, age, move)
page.render(os.path.join(OUT, "ch4_01_人力资源看板.html"))
print("已生成: output/ch4_01_人力资源看板.html")
