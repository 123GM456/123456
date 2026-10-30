# 课程作业仓库（2026 秋）

本仓库收录两门课程的数据分析作业，各自独立、互不依赖，可单独复现：

| 目录 | 课程 | 内容 | 报告 |
| --- | --- | --- | --- |
| [商业数据分析/](商业数据分析/) | 《商业数据分析》期末大作业 | 全球宏观经济分析（世界银行 WDI，217 个经济体 × 2000–2024，6 个分析模型 + 22 张交互图 + 1 个联动大屏 + 8 张论文配图） | `期末大论文_基于世界银行开放数据的全球宏观经济分析.docx` |
| [大数据分析/](大数据分析/) | 《大数据分析》课程作业 | Excel 数据可视化复现（39 张 pyecharts 图表：30 静态 + 7 动态 + 2 看板，附离线总览页） | `excel-charts/index.html` |

## 一、商业数据分析（宏观经济方向）

**题目**：基于世界银行开放数据的全球宏观经济分析

**一句话结论**：2000—2024 年全球经济重心持续东移，中国 GDP 全球份额从 3.64% 升至 16.93%，但增速自 2007 年 14.15% 的峰值回落到 2024 年 4.96%，仍高于全球加权平均 2.86%。

**技术栈**：Python 3.10+ / pandas / numpy / pyecharts / Pillow / python-docx（**未使用 Power BI、Tableau、FineBI；未使用爬虫**）

**运行**：

```powershell
cd 商业数据分析
pip install -r requirements.txt
python run_all.py          # 依次执行 01→07，约 10 秒产出全部结果
python run_all.py 2 3      # 也可只重跑指定步骤
```

**产物**：`outputs/figs`（22 张交互图）、`outputs/figs_png`（8 张 150dpi 论文配图）、`outputs/dashboard.html`（交互大屏，5 个控制器 + 8 个联动组件）、`outputs/index.html`（图表索引页）、`outputs/models`（模型结果 CSV 与 `conclusions.json`）、论文 docx。

**数据合规**：8 个 WDI 指标全部来自世界银行官方 API 下载包（`data/raw`），文件内置 `Metadata_Country` / `Metadata_Indicator`，可核对国别、区域与指标口径；获取方式、授权与清洗口径见 [商业数据分析/docs/合规声明.md](商业数据分析/docs/合规声明.md)。

明细说明见 [商业数据分析/README.md](商业数据分析/README.md)。

## 二、大数据分析

**内容**：以《Excel 数据可视化——从图表到数据大屏》（清华大学出版社）教材配套示例为蓝本，用 **Python + pyecharts** 复现 39 张图表——第二章 30 张静态图表（渐变柱形图、蝴蝶图、瀑布图、雷达图、甘特图、词云等）、第三章 7 张动态图表（Timeline）、第四章 2 个数据看板，并生成可离线浏览的静态总览页。

**运行**（每个图表脚本独立执行，HTML 输出到 `output/`）：

```powershell
cd 大数据分析/excel-charts
pip install -r requirements.txt
python chapter2/chart01_渐变柱形图.py     # 单张图表
python chapter4/chart02_销售数据大屏.py   # 数据看板
python add_nav.py                        # 重跑图表后补回「上一张/下一张」导航
```

总览入口：`excel-charts/index.html`。

教材原始数据（xlsx/pptx，约 11 MB）属版权材料，已通过 `大数据分析/.gitignore` 排除，不入库。

## 三、仓库约定

- `.gitignore` 只排除「可再生成」的环境与缓存：Python 缓存、虚拟环境、IDE 配置、Office 临时锁文件、日志、一次性调试脚本。
- 数据、代码、图表产物与论文一律入库，保证 clone 下来即可复现与查看，无需联网。
- 两个作业的入口脚本都只用相对路径定位项目根目录，移动或改名仓库文件夹不影响运行。

## 四、环境

| 依赖 | 版本要求 | 用途 |
| --- | --- | --- |
| pandas / numpy | ≥ 2.0 / ≥ 1.24 | 数据处理与建模 |
| pyecharts | ≥ 2.0 | 22 张交互图 + 大屏（本地 ECharts 离线渲染） |
| Pillow | ≥ 10.0 | 论文 8 张 150dpi 静态配图 |
| python-docx | ≥ 1.1 | 按学校模板生成论文 docx |
| Node.js | ≥ 18（可选） | 运行 `tests/test_dashboard.js` 大屏冒烟测试 |

单机实测：Python 3.13.2 与 3.12 双解释器混跑（`run_all.py` 会自动探测哪个解释器装齐了所需库）。
