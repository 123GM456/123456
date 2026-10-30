# -*- coding: utf-8 -*-
"""
07_index.py — 生成图表索引页 outputs/index.html
================================================
为什么要它：作业要求"图表统一命名 + 图表索引（附录 C）"。
本脚本扫描 outputs/figs 与 outputs/figs_png，按文件名里的图号自动排序，
生成一个可点击预览的索引页：左侧目录 + 右侧 iframe 预览（HTML 图）或
直接嵌图（PNG）。索引页本身也离线可用（相对路径 + 本地 echarts）。
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(BASE, "outputs", "figs")
PNGS = os.path.join(BASE, "outputs", "figs_png")
OUT = os.path.join(BASE, "outputs", "index.html")

# 图表说明：key 为文件名前缀（figNN / paper_figN）
DESC = {
    "fig01": ("折线图", "全球与中国实际 GDP 增速对比（2000–2024）"),
    "fig02": ("柱形图", "2024 年 GDP 前十国的规模与全球份额"),
    "fig03": ("堆叠面积图", "七大区域 GDP 份额的长期演变"),
    "fig04": ("环形饼图", "2024 年各区域 GDP 份额构成"),
    "fig05": ("玫瑰图", "四档收入分组的 GDP 份额（高收入占 64.49%）"),
    "fig06": ("散点图", "人均 GDP 与增速的关系（气泡=经济规模）"),
    "fig07": ("雷达图", "八个重点国家的六维宏观经济画像"),
    "fig08": ("热力图", "八国 2000–2024 年增速矩阵"),
    "fig09": ("箱线图", "各区域增速分布与离群国家"),
    "fig10": ("仪表盘", "CR10 集中度与中国份额双指针"),
    "fig11": ("矩形树图", "区域→国家的 GDP 下钻结构"),
    "fig12": ("桑基图", "收入分组到地理区域的 GDP 流向"),
    "fig13": ("漏斗图", "ABC 三类国家的规模衰减"),
    "fig14": ("平行坐标图", "K-Means 五个群体的质心画像"),
    "fig15": ("双轴组合图", "【模型 M1】中国增速（柱）与全球份额（线）"),
    "fig16": ("帕累托图", "【模型 M2】前 20 国贡献 81.29%，80% 分界在第 19 国"),
    "fig17": ("分组柱形图", "【模型 M2】ABC 三类的国家数与份额对比"),
    "fig18": ("气泡矩阵图", "【模型 M3】波士顿矩阵四象限（份额×复合增速）"),
    "fig19": ("分类散点图", "【模型 M4】K-Means 五群体分布"),
    "fig20": ("双轴诊断图", "【模型 M4】k 的选择：肘部法 SSE + 轮廓系数"),
    "fig21": ("预测区间图", "【模型 M5】中国 2025–2027 年 GDP 点预测与 95% 置信区间"),
    "fig22": ("误差柱形图", "【模型 M5】2022–2024 年滚动回测误差"),
    "paper_fig1": ("论文配图", "全球与中国实际增速（静态 150dpi）"),
    "paper_fig2": ("论文配图", "七大区域份额演变（堆叠面积）"),
    "paper_fig3": ("论文配图", "帕累托图与 80% 分界线"),
    "paper_fig4": ("论文配图", "波士顿矩阵四象限"),
    "paper_fig5": ("论文配图", "K-Means 五群体分群"),
    "paper_fig6": ("论文配图", "中国 GDP 预测与置信带"),
    "paper_fig7": ("论文配图", "滚动回测误差"),
    "paper_fig8": ("论文配图", "收入分组环形结构"),
}

TPL_TYPES = ["折线图", "柱形图", "堆叠面积图", "环形饼图", "玫瑰图", "散点图",
             "雷达图", "热力图", "箱线图", "仪表盘", "矩形树图", "桑基图",
             "漏斗图", "平行坐标图"]


def main():
    html_figs = sorted(f for f in os.listdir(FIGS) if f.endswith(".html"))
    png_figs = sorted(f for f in os.listdir(PNGS) if f.endswith(".png"))

    def key(name):
        m = re.match(r"(paper_fig|fig)(\d+)", name)
        return (0 if m and m.group(1) == "fig" else 1, int(m.group(2)) if m else 999)

    html_figs.sort(key=key)
    png_figs.sort(key=key)

    rows = []
    for i, f in enumerate(html_figs, start=1):
        pre = f.split("_")[0]
        typ, desc = DESC.get(pre, ("—", f))
        rows.append((f"图 {i:02d}", f, typ, desc, "html"))
    for i, f in enumerate(png_figs, start=1):
        pre = "_".join(f.split("_")[:2])
        typ, desc = DESC.get(pre, ("—", f))
        rows.append((f"配图 {i}", f, typ, desc, "png"))

    n_tpl = sum(1 for r in rows if r[4] == "html" and r[0] <= "图 14")
    cards = []
    for num, f, typ, desc, kind in rows:
        src = f"figs/{f}" if kind == "html" else f"figs_png/{f}"
        body = (f'<iframe src="{src}" title="{num}"></iframe>' if kind == "html"
                else f'<img src="{src}" alt="{num}">')
        cards.append(f'''
    <section class="card" id="{f}">
      <h3>{num} · {typ}</h3>
      <p class="d">{desc}</p>
      <p class="p">{src}</p>
      <div class="view">{body}</div>
    </section>''')

    nav = "\n".join(
        f'    <li><a href="#{f}"><b>{num}</b> {desc[:26]}</a></li>'
        for num, f, typ, desc, kind in rows)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>图表索引 · 全球宏观经济分析</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family:"Microsoft YaHei","PingFang SC",sans-serif;
         background:#f5f7fa; color:#2c3e50; }}
  header {{ background:linear-gradient(135deg,#31547f,#4a7ab5); color:#fff;
           padding:26px 32px; }}
  header h1 {{ margin:0 0 6px; font-size:22px; }}
  header p {{ margin:0; opacity:.85; font-size:13px; }}
  .wrap {{ display:flex; align-items:flex-start; }}
  nav {{ position:sticky; top:0; width:290px; height:100vh; overflow:auto;
        background:#fff; border-right:1px solid #e3e8ee; padding:14px 0; }}
  nav h2 {{ font-size:13px; color:#7b8794; margin:10px 18px 8px; }}
  nav ul {{ list-style:none; margin:0; padding:0; }}
  nav li a {{ display:block; padding:7px 18px; font-size:12.5px; color:#34495e;
             text-decoration:none; border-left:3px solid transparent; }}
  nav li a:hover {{ background:#eef4fb; border-left-color:#4a7ab5; }}
  nav li b {{ color:#4a7ab5; margin-right:6px; }}
  main {{ flex:1; padding:22px 26px; }}
  .summary {{ display:flex; gap:14px; flex-wrap:wrap; margin-bottom:18px; }}
  .kpi {{ flex:1; min-width:150px; background:#fff; border-radius:10px;
         padding:14px 16px; box-shadow:0 1px 4px rgba(0,0,0,.07); }}
  .kpi b {{ display:block; font-size:22px; color:#31547f; }}
  .kpi span {{ font-size:12px; color:#7b8794; }}
  .card {{ background:#fff; border-radius:10px; margin-bottom:18px;
          box-shadow:0 1px 4px rgba(0,0,0,.07); overflow:hidden; }}
  .card h3 {{ margin:0; padding:13px 18px 4px; font-size:15px; }}
  .card .d {{ margin:0; padding:0 18px 6px; font-size:13px; color:#516170; }}
  .card .p {{ margin:0; padding:0 18px 10px; font-size:11px; color:#a0aab4;
             font-family:Consolas,monospace; }}
  .view {{ border-top:1px solid #eef1f5; background:#fbfcfe; }}
  iframe {{ width:100%; height:520px; border:0; display:block; }}
  img {{ width:100%; display:block; }}
  footer {{ padding:16px 26px 40px; font-size:12px; color:#8a949e; }}
</style>
</head>
<body>
<header>
  <h1>图表索引 · 基于世界银行开放数据的全球宏观经济分析</h1>
  <p>共 {len(rows)} 个图表 · 交互图 {len(html_figs)} 张（模板复现 14 种图表类型 + 业务模型图 8 张）
     · 论文静态配图 {len(png_figs)} 张（150 dpi）</p>
</header>
<div class="wrap">
  <nav>
    <h2>目录</h2>
    <ul>
{nav}
    </ul>
  </nav>
  <main>
    <div class="summary">
      <div class="kpi"><b>{len(html_figs)}</b><span>交互图表（HTML）</span></div>
      <div class="kpi"><b>14</b><span>模板图表类型</span></div>
      <div class="kpi"><b>6</b><span>商业分析模型</span></div>
      <div class="kpi"><b>8</b><span>大屏联动组件</span></div>
    </div>
    <div class="card" style="padding:0">
      <h3 style="padding-bottom:10px">交互大屏</h3>
      <p class="d" style="padding-bottom:8px">
        5 个筛选控制器 + 8 个联动组件，支持区域环形图 / 排行榜 / 群体柱 / 明细表的反向联动。
        <a href="dashboard.html" target="_blank">单独打开大屏 →</a></p>
      <div class="view"><iframe src="dashboard.html" title="dashboard"></iframe></div>
    </div>
{"".join(cards)}
  </main>
</div>
<footer>数据来源：世界银行 World Development Indicators（官方开放数据）。
图表由 Python + pyecharts / Pillow 生成，未使用任何 BI 商业软件或 Excel 截图。</footer>
</body>
</html>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  OK index.html  共索引 {len(rows)} 个图表（HTML {len(html_figs)} / PNG {len(png_figs)}）")


if __name__ == "__main__":
    main()
