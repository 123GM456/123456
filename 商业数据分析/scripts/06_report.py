# -*- coding: utf-8 -*-
"""
06_report.py —— 按学校官方模板生成期末论文 docx

思路：以 `作业要求/5、《商业数据分析》 - 期末大作业模板.docx` 为容器，
1) 删除全部红色提示文字（整段皆红者整段删除）；
2) 填封面与文章首页的题目、作者、摘要、关键词；
3) 把 `docs/paper_content.json` 里的正文按小节顺序灌进模板的每个二级标题下；
4) 参考文献样例行替换为 11 条真实文献，附录 A/B/C 依次填充。

正文的源文件是 `docs/paper_content.json`（结构化文本：段落、列表、题注、表格的
表头/数据/列宽、图的题注），本脚本只负责排版与插图（PNG 取自 outputs/figs_png）。
这样论文正文可以独立于 docx 编辑，脚本里不写 1 万多字的散文。
"""
from __future__ import annotations

import copy
import json
import re
import sys
import unicodedata
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "作业要求" / "5、《商业数据分析》 - 期末大作业模板.docx"
CONTENT = ROOT / "docs" / "paper_content.json"
OUT = ROOT / "期末大论文_基于世界银行开放数据的全球宏观经济分析.docx"
FIGS = ROOT / "outputs" / "figs_png"

TITLE = "基于世界银行开放数据的全球宏观经济分析"
COLLEGE = "数据科学学院"
MAJOR = "大数据242"
STUNO = "2023451685215"
DATE = "2026 年 11 月 4 日"
AUTHOR = "郑嘉豪"
NAME = "郑嘉豪"

ABSTRACT = (
    "本文以世界银行 WDI 的 8 个核心指标、217 个经济体、2000—2024 年面板数据为对象，"
    "完整走通「合规获取—清洗治理—六模型建模—双套可视化—商业解读」的分析链路。"
    "先用规则阈值与 3×IQR 处理异常值与结构性缺失，形成长表、宽表与结论快照三层资产；"
    "再用趋势对比、帕累托 ABC、波士顿矩阵、K-Means 聚类、Holt 线性趋势预测与结构演变六个模型，"
    "依次回答增长中枢、集中度、国家定位、群体画像、规模预测与结构重排六个问题。"
    "结果显示：全球加权增速的三个十年段均值在 2.41%—3.08% 震荡，中国 2024 年增速 4.96%、"
    "高出全球 2.10 个百分点，但增速差已从 2010 年代的 6 个百分点收窄至 2 个百分点；"
    "前 19 国贡献 80% 的全球产出，前 10 国份额由 73.82% 降至 67.22%；"
    "波士顿矩阵与 K-Means 聚类分别以专家规则与数据驱动，把中国、印度识别为高份额高增速经济体；"
    "Holt 模型预测中国 2025—2027 年 GDP 为 19.71、20.51、21.31 万亿美元，回测 MAPE 7.65%。"
    "据此提出按 ABC 分预算、按群体匹配进入方式等五条可操作建议。"
)

KEYWORDS = "世界银行 WDI；数据合规获取；波士顿矩阵；K-Means 聚类；Holt 线性趋势预测"

# 模板中 23 个二级标题的锚点（按文档顺序），用于顺序配对旧文小节
ANCHORS = [
    "研究背景",
    "研究目的",
    "研究意义",
    "数据源介绍",
    "合规获取方式",
    "数据来源合规声明",
    "数据集概述",
    "数据清洗",
    "数据转换",
    "数据整合",
    "模型选型",
    "参数与阈值设定依据",
    "模型计算与验证",
    "数据探索性分析",
    "可视化模板复现",
    "业务模型图",
    "交互式可视化大屏",
    "案例背景",
    "结果解读",
    "商业建议",
    "研究结论",
    "局限性与展望",
    "AI 使用披露",
]

FIG_MAP = [  # (题注关键词, 文件名)
    ("帕累托", "paper_fig3_帕累托图.png"),
    ("波士顿", "paper_fig4_波士顿矩阵.png"),
    ("K-Means", "paper_fig5_KMeans分群.png"),
    ("置信区间", "paper_fig6_中国GDP预测.png"),
    ("回测", "paper_fig7_回测误差.png"),
    ("区域", "paper_fig2_区域份额演变.png"),
    ("收入分组", "paper_fig8_收入分组结构.png"),
    ("增速", "paper_fig1_全球与中国GDP增速.png"),
]


# ---------------------------------------------------------------- 基础排版工具
def set_font(run, name="宋体", size=12, bold=None, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)
    return run


def make_para(text="", size=None, bold=False, indent=True, align=None,
              name="宋体", space_before=0, space_after=0, line=1.5,
              left=0.0, first=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if first is not None:
        pf.first_line_indent = Pt(first)
    elif indent and size is not None:
        pf.first_line_indent = Pt(size * 2)
    pf.left_indent = Cm(left) if left else None
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        if size is None:                 # 继承 Normal：五号宋体
            r.font.name = name
            rpr = r._element.get_or_add_rPr()
            rpr.get_or_add_rFonts().set(qn("w:eastAsia"), name)
            r.font.bold = True if bold else None
        else:
            set_font(r, name=name, size=size, bold=bold)
    return p


def text_units(s: str) -> int:
    """按「全角算 2、半角算 1」估算显示宽度，用于保持下划线行长度不变。"""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def fill_blank(par, value: str) -> None:
    """把值填进模板的下划线空白。

    模板的空白是一串「带下划线的全角空格」（楷体_GB2312 14pt）。这里不新建 run，
    而是把值写进第一个空白 run（保留它原有的字体、字号与下划线），
    再按原行的显示宽度补空格、删掉多余的空白 run——字体、下划线、行宽三者都不变。
    """
    runs = list(par.runs)
    colons = [i for i, r in enumerate(runs) if "：" in r.text or ":" in r.text]
    cut = max(colons) if colons else len(runs) - 1
    blanks = runs[cut + 1:]

    if not blanks:                      # 模板没留空白时，追加到段尾并复制标签格式
        run = par.add_run(value)
        if runs:
            run._element.insert(0, copy.deepcopy(runs[cut]._element.get_or_add_rPr()))
        return

    total = sum(text_units(r.text) for r in blanks)
    pad_units = max(0, total - text_units(value))
    pad = "　" * (pad_units // 2) + (" " if pad_units % 2 else "")

    blanks[0].text = value + pad        # 只改文字，rPr（楷体 + 下划线）原样保留
    for r in blanks[1:]:
        r._element.getparent().remove(r._element)


def insert_after(anchor, element):
    """把 element 插到 anchor 之后，返回新游标。"""
    anchor.addnext(element)
    return element


# ---------------------------------------------------------------- 1. 删红色
RED = {"FF0000"}


def is_red(run):
    try:
        c = run.font.color
    except Exception:
        return False
    if c is None or c.rgb is None:
        return False
    return str(c.rgb).upper() in RED


def strip_red(document):
    removed_paras = 0
    for p in list(document.paragraphs):
        hit = False
        for r in list(p.runs):
            if is_red(r):
                hit = True
                r._element.getparent().remove(r._element)
        if hit and not p.text.strip():
            p._element.getparent().remove(p._element)
            removed_paras += 1
    return removed_paras


# ---------------------------------------------------------------- 2. 正文源
def load_content():
    """读取 docs/paper_content.json，返回 (小节字典, 参考文献, 附录字典)。

    小节字典的 key 为 S0..S22，与 ANCHORS 顺序一一对应；
    每个块是 (kind, payload)：p/b/sub/cap/note/code/h3/fig/tbl。
    """
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    sections = {
        key: [(b["k"], b["t"]) for b in blocks]
        for key, blocks in data["sections"].items()
    }
    refs = list(data["references"])
    appendix = {
        letter: [(b["k"], b["t"]) for b in blocks]
        for letter, blocks in data["appendix"].items()
    }
    return sections, refs, appendix


def fig_file(caption: str) -> str:
    for kw, name in FIG_MAP:
        if kw in caption:
            return name
    return FIG_MAP[-1][1]


# ---------------------------------------------------------------- 3. 灌入模板
def find_para(prefix):
    for p in doc.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    raise KeyError(prefix)


MAX_TABLE_CM = 14.4        # 正文版心 14.66cm，留 0.26cm 余量


def build_table(spec):
    """按 JSON 里的表头/行/列宽重建三线表（Table Grid 边框 + 居中单元格）。"""
    headers, rows, widths = spec["headers"], spec["rows"], spec["widths"]
    ncol = len(headers)
    total = sum(widths) or MAX_TABLE_CM
    scale = min(1.0, MAX_TABLE_CM / total)
    widths = [w * scale for w in widths]

    tbl = doc.add_table(rows=len(rows) + 1, cols=ncol)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    for j, w in enumerate(widths):
        tbl.columns[j].width = Cm(w)

    for i, row in enumerate([headers] + rows):
        for j in range(ncol):
            cell = tbl.cell(i, j)
            cell.width = Cm(widths[j])
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf = p.paragraph_format
            pf.first_line_indent = Pt(0)
            pf.space_before = Pt(2)
            pf.space_after = Pt(2)
            pf.line_spacing = 1.15
            set_font(p.add_run(row[j] if j < len(row) else ""), size=9.5)
    return tbl._element


def emit(cursor, blocks, body):
    """在 cursor 之后依次插入块，返回新的 cursor 元素。"""
    for kind, payload in blocks:
        if kind == "fig":
            p = make_para(align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, line=1.0,
                          space_before=6, space_after=2)
            p.add_run().add_picture(str(FIGS / fig_file(payload)),
                                    width=Cm(12.5 if "收入分组" in payload else 14.2))
            cursor = insert_after(cursor, p._element)
            cap = make_para(payload, size=10.5, bold=True, indent=False,
                            align=WD_ALIGN_PARAGRAPH.CENTER, space_before=3,
                            space_after=8, line=1.15)
            el = cap._element
        elif kind == "cap":
            p = make_para(payload, size=10.5, bold=True, indent=False,
                          align=WD_ALIGN_PARAGRAPH.CENTER, space_before=3,
                          space_after=6, line=1.15)
            el = p._element
        elif kind == "note":
            p = make_para(payload, size=9, indent=False, space_before=2,
                          space_after=6, line=1.15)
            for r in p.runs:
                r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
            el = p._element
        elif kind == "code":
            p = make_para(payload, size=8.5, indent=False, name="Consolas",
                          line=1.0, left=0.4, space_before=2, space_after=6)
            el = p._element
        elif kind == "b":
            p = make_para("· " + payload, size=None, indent=False, left=0.85,
                          first=-0.85, space_after=2)
            el = p._element
        elif kind == "sub":
            p = make_para(payload, size=10.5, bold=True, indent=False,
                          space_before=6, space_after=2)
            el = p._element
        elif kind == "h3":
            p = doc.add_paragraph(payload, style="Heading 3")
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            el = p._element
        elif kind == "tbl":
            el = build_table(payload)
        else:  # 普通正文：沿用模板 Normal（五号宋体、首行缩进 2 字符、1.5 倍行距）
            p = make_para(payload, size=None, indent=False, space_after=0)
            el = p._element
        cursor = insert_after(cursor, el)
    return cursor


def main():
    global doc
    if not TPL.exists():
        sys.exit(f"模板不存在：{TPL}")
    if not CONTENT.exists():
        sys.exit(f"缺少正文源文件：{CONTENT}")

    doc = Document(TPL)
    n_red = strip_red(doc)
    print(f"[06] 删除红色提示文字：{n_red} 个整段（其余段内的红色 run 已逐段剔除）")

    # ---- 封面：题目 / 学院 / 专业班级 / 完成日期
    cover = {
        "题　　目：": TITLE,
        "学　　院：": COLLEGE,
        "专业班级：": MAJOR,
        "学　　号：": STUNO,
        "姓　　名：": NAME,
        "完成日期：": DATE,
    }
    filled = 0
    for p in doc.paragraphs[:12]:
        t = p.text
        for key, val in cover.items():
            if t.startswith(key):
                fill_blank(p, val)
                filled += 1
    print(f"[06] 封面填写 {filled} 项（沿用模板的下划线空白与楷体）")

    # ---- 文章首页：论文题目 / 作者
    p = find_para("论文题目")
    for r in p.runs:                       # 题目标签与标题统一成三号黑体加粗
        set_font(r, name="黑体", size=16, bold=True)
    set_font(p.add_run("：" + TITLE), name="黑体", size=16, bold=True)
    p = find_para("作者")
    run = p.add_run("：" + AUTHOR)          # 作者行沿用标签 run 的原格式（不另设字体字号）
    if p.runs:
        run._element.insert(0, copy.deepcopy(p.runs[0]._element.get_or_add_rPr()))

    # ---- 摘要（标签四号黑体，内容小四宋体 1.5 倍行距）
    p = find_para("摘要")
    for r in p.runs:
        if r.text.strip() in ("摘要", "关键词"):
            set_font(r, name="黑体", size=14)
    tail = p.runs[-1] if p.runs else None          # 结尾的「．」
    run = p.add_run(ABSTRACT)
    set_font(run, size=12)
    if tail is not None and tail.text.strip() in ("．", "."):
        tail._element.addprevious(run._element)    # 摘要放在句号之前
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.5

    # ---- 关键词
    p = find_para("关键词")
    for r in p.runs:
        if r.text.strip() == "关键词":
            set_font(r, name="黑体", size=14)
    set_font(p.add_run(KEYWORDS + "．"), size=12)
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.5

    # ---- 正文：把 JSON 里的各小节灌进模板对应的二级标题下
    sections, refs, appendix = load_content()
    n_block = sum(len(v) for v in sections.values())
    print(f"[06] 正文源：{len(sections)} 个小节，{n_block} 块")

    # 必须按「二级标题」精确定位：正文里「数据清洗与治理」这类一级标题
    # 会与「数据清洗」前缀撞车，用 startswith 查段落就会插错位置。
    h2_paras = [p for p in doc.paragraphs if p.style.name == "Heading 2"]
    if len(h2_paras) != len(ANCHORS):
        sys.exit(f"模板二级标题数 {len(h2_paras)} 与预期 {len(ANCHORS)} 不符")
    for i, (key, anchor) in enumerate(zip(ANCHORS, h2_paras)):
        if not anchor.text.strip().startswith(key):
            sys.exit(f"第 {i+1} 个二级标题不匹配：期望「{key}」，实际「{anchor.text}」")
        body = sections.get(f"S{i}", [])
        emit(anchor._element, body, doc.element.body)
        print(f"  · {key:<18} 插入 {len(body):>2} 块")

    # ---- 参考文献：替换样例行
    raw = next(p for p in doc.paragraphs if p.text.strip().startswith("[1] ***"))
    cursor = raw._element
    for text in refs:
        p = make_para(text, size=10.5, indent=False, line=1.3, space_after=3,
                      left=0.75, first=-0.75)
        cursor = insert_after(cursor, p._element)
    raw._element.getparent().remove(raw._element)
    print(f"[06] 参考文献：{len(refs)} 条（示例行已删除）")

    # ---- 附录 A/B/C
    for letter in ("A", "B", "C"):
        anchor = find_para(f"{letter} ")
        body = appendix.get(letter, [])
        emit(anchor._element, body, doc.element.body)
        print(f"  · 附录 {letter}          插入 {len(body):>2} 块")

    doc.save(OUT)

    # ---- 自检
    chk = Document(OUT)
    cn = sum(len(re.findall(r"[\u4e00-\u9fff]", p.text)) for p in chk.paragraphs)
    heads = [(p.style.name, p.text.strip()) for p in chk.paragraphs
             if p.style.name.startswith("Heading")]
    reds = sum(1 for p in chk.paragraphs for r in p.runs if is_red(r))
    print(f"\n[06] 输出：{OUT}")
    print(f"     段落 {len(chk.paragraphs)}  表格 {len(chk.tables)}  "
          f"图片 {len(chk.inline_shapes)}  中文字 {cn}")
    print(f"     标题 {len(heads)} 个；残留红色 run {reds} 个")
    for name, text in heads:
        print(f"       {name[-1]} │ {text}")


if __name__ == "__main__":
    main()
