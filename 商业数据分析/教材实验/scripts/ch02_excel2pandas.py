"""第 2 章 Excel 函数与数据透视表 · pandas 迁移

教材原做法
----------
第 2 章前半部分（1、分析的基础范式）用 Excel 讲"分析方法的实现"：
- IF / IFERROR / AND / OR：写 `=IF(AND(数学>=60,计算机>=60,英语>=60),"通过","未通过")`
- VLOOKUP：拿商品编码去商品表里查名称
- COUNTIF / COUNTIFS：打卡表里数"迟到"和"旷课"的次数
- SUMIF / SUMIFS：按会计科目汇总传票金额
- 数据透视表：拖字段做分组汇总

迁移思路
--------
Excel 是「单元格公式逐行计算」，pandas 是「整列向量化计算」，一一对应：

| Excel                    | pandas                                    |
|--------------------------|-------------------------------------------|
| `IF(条件, 真, 假)`       | `np.where(条件, 真, 假)`                  |
| `IFERROR(x, 默认)`       | `x.fillna(默认)` / `np.nan_to_num`        |
| `AND(a,b)` / `OR(a,b)`   | `(a) & (b)` / `(a) \| (b)`                |
| `VLOOKUP(键, 表, 列, 0)` | `df.merge(表, on="键", how="left")`       |
| `COUNTIF(区域,"x")`      | `(df[列] == "x").sum()`                   |
| `SUMIF(区域,"x",求和区)` | `df.loc[df[列]=="x", 求和列].sum()`       |
| 数据透视表               | `df.pivot_table(index=, columns=, aggfunc=)` |

运行：python scripts/ch02_excel2pandas.py
输出：outputs/ch02_*.csv
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch02")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

PASS_LINE = 60  # 教材的及格线


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA, f"{name}.csv"))


def case_if() -> pd.DataFrame:
    """IF + AND/OR：三门是否全部通过 / 是否至少一门通过 / 等级评价。"""
    df = read("excel_if").dropna(subset=["学号", "姓名"]).copy()
    math_, cs, en = df["数学"], df["计算机"], df["英语"]

    pass_all = (math_ >= PASS_LINE) & (cs >= PASS_LINE) & (en >= PASS_LINE)
    pass_any = (math_ >= PASS_LINE) | (cs >= PASS_LINE) | (en >= PASS_LINE)
    df["评价（三门均通过）"] = np.where(pass_all, "通过", "未通过")
    df["评价（三门之一通过）"] = np.where(pass_any, "通过", "未通过")

    # 教材用层层嵌套 IF 算等级，这里用 np.select（更接近 DAX 的 SWITCH）
    avg = df[["数学", "计算机", "英语"]].mean(axis=1)
    df["平均分"] = avg.round(1)
    df["等级"] = np.select(
        [avg >= 90, avg >= 80, avg >= 70, avg >= 60],
        ["A", "B", "C", "D"], default="E")
    print("\n[1] IF + AND/OR → np.where / np.select（11 名学生）")
    print(df[["姓名", "数学", "计算机", "英语", "平均分", "等级",
              "评价（三门均通过）", "评价（三门之一通过）"]].to_string(index=False))
    return df


def case_vlookup() -> pd.DataFrame:
    """VLOOKUP → merge：明细表 100 行只有编码，用 3314 行的商品字典补名称。"""
    detail = read("excel_vlookup").drop(columns=["item_name"])
    mapping = read("excel_vlookup_map")
    # 编码在两边都是 float（因为原表有空格），统一转成 Int 再连接，避免 10010.0 != 10010
    detail["item_code"] = pd.to_numeric(detail["item_code"], errors="coerce").astype("Int64")
    mapping["item_code"] = pd.to_numeric(mapping["item_code"], errors="coerce").astype("Int64")

    merged = detail.merge(mapping, on="item_code", how="left")
    merged["item_name"] = merged["item_name"].fillna("未匹配")  # 相当于 IFERROR
    hit = (merged["item_name"] != "未匹配").mean()
    print(f"\n[2] VLOOKUP → merge（明细 {len(detail)} 行 × 字典 {len(mapping)} 行）")
    print(f"    匹配成功率 {hit:.2%}")
    print(merged[["item_code", "item_name", "qty", "amount"]].head(6).to_string(index=False))
    return merged


def case_countif() -> pd.DataFrame:
    """COUNTIF → 布尔求和：打卡表 a=出勤 / b=迟到 / c=旷课。"""
    df = read("excel_countif")
    df = df.rename(columns={df.columns[0]: "学号"})
    day_cols = [c for c in df.columns if str(c).isdigit()]
    marks = df[day_cols]

    df["迟到次数"] = (marks == "b").sum(axis=1)
    df["旷课次数"] = (marks == "c").sum(axis=1)
    df["出勤次数"] = (marks == "a").sum(axis=1)
    df["考勤得分"] = (df["出勤次数"] * 100 + df["迟到次数"] * 60) / len(day_cols)
    print(f"\n[3] COUNTIF → 布尔求和（{len(df)} 名学生 × {len(day_cols)} 天）")
    print(df[["学号", "出勤次数", "迟到次数", "旷课次数", "考勤得分"]]
          .sort_values("考勤得分").to_string(index=False))
    return df


def case_sumif() -> dict[str, pd.DataFrame]:
    """SUMIF/SUMIFS → groupby：按会计科目、按借贷方向汇总传票金额。"""
    df = read("excel_sumif")
    df.columns = ["传票号码", "传票日期", "会计科目", "借贷", "银行名称",
                  "支票号码", "客户名称", "金额", "摘要"]
    df = df.dropna(subset=["会计科目"])
    # 原表里混着表头行（会计科目="会计科目"、借贷="借/贷"），先剔掉
    df = df[(df["会计科目"] != "会计科目") & (~df["借贷"].isin(["借/贷"]))]
    df["金额"] = pd.to_numeric(df["金额"], errors="coerce")

    by_subject = (df.groupby("会计科目")
                  .agg(笔数=("金额", "size"), 金额合计=("金额", "sum"))
                  .reset_index().sort_values("金额合计", ascending=False))
    # SUMIFS 两个条件：科目 + 借贷方向
    cross = df.pivot_table(index="会计科目", columns="借贷", values="金额",
                           aggfunc="sum", fill_value=0)
    print(f"\n[4] SUMIF/SUMIFS → groupby / pivot_table（{len(df)} 条传票）")
    print(by_subject.to_string(index=False))
    print("\n    借贷方向 × 科目（SUMIFS 双条件）：")
    print(cross.to_string())
    return {"ch02_sumif_by_subject": by_subject,
            "ch02_sumif_cross": cross.reset_index()}


def case_pivot() -> pd.DataFrame:
    """数据透视表 → pivot_table：班级 × 性别 的平均分与人数。"""
    df = read("excel_if").dropna(subset=["学号", "姓名"])
    avg = (df.assign(总分=df[["数学", "计算机", "英语"]].sum(axis=1))
           .pivot_table(index="班级", columns="性别",
                        values=["数学", "计算机", "英语"], aggfunc="mean"))
    counts = df.pivot_table(index="班级", columns="性别", values="姓名",
                            aggfunc="count", fill_value=0)
    print("\n[5] 数据透视表 → pivot_table（班级 × 性别 平均分）")
    print(avg.round(1).to_string())
    print("\n    人数：")
    print(counts.to_string())
    flat = avg.round(2).reset_index()
    flat.columns = ["_".join([str(x) for x in c if x]) for c in flat.columns]
    return flat


def main() -> int:
    print("=" * 78)
    print("第 2 章 · Excel 函数与数据透视表 → pandas")
    print("=" * 78)
    results = {
        "ch02_if": case_if(),
        "ch02_vlookup": case_vlookup(),
        "ch02_countif": case_countif(),
        "ch02_pivot": case_pivot(),
    }
    results.update(case_sumif())
    for name, df in results.items():
        path = os.path.join(OUT, f"{name}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  → {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
