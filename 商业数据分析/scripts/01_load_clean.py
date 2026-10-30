# -*- coding: utf-8 -*-
"""
01_load_clean.py — 数据加载与清洗治理
=====================================
输入：data/raw/ 下 8 个世界银行 WDI 官方下载包（每个包 1 个指标 + 2 个元数据文件）
输出：data/clean/master.csv          长表主表（国家-年份-指标-值）
      data/clean/country_year.csv    宽表主表（国家-年份 × 8 指标，建模用）
      data/clean/gdp_wide.csv        GDP 现价宽表（国家 × 年份，帕累托/矩阵用）
      data/clean/data_dictionary.csv 数据字典
      data/clean/report.json         清洗质量报告

治理流程：读取 → 剔除国家聚合体 → 宽转长 → 年份裁剪 → 重复值去重
          → 类型统一 → 规则+统计双重异常值识别 → 缺失盘点 → 派生指标
"""
import json
import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
CLEAN = os.path.join(BASE, "data", "clean")

# 指标注册表：WDI 指标代码 → (中文名, 单位, 业务含义)
INDICATORS = {
    "NY.GDP.MKTP.CD": ("GDP现价", "现价美元", "经济体总量，衡量市场规模"),
    "NY.GDP.MKTP.KD.ZG": ("GDP增长率", "%", "不变价年增长率，衡量增长动能"),
    "NY.GDP.PCAP.KD.ZG": ("人均GDP增长率", "%", "剔除人口因素的真实增长"),
    "SP.POP.TOTL": ("总人口", "人", "市场人口基数"),
    "NE.TRD.GNFS.ZS": ("贸易占GDP比重", "%", "对外开放度/贸易依存度"),
    "NE.EXP.GNFS.ZS": ("出口占GDP比重", "%", "外需依赖度"),
    "GC.DOD.TOTL.GD.ZS": ("政府债务占GDP", "%", "财政风险敞口"),
    "SL.UEM.TOTL.ZS": ("失业率", "%", "劳动力市场景气度"),
}

YEAR_MIN, YEAR_MAX = 2000, 2024

# 规则型异常阈值（业务上不可能或明显失真的取值区间）
RULES = {
    "GDP增长率": (-50.0, 50.0),
    "人均GDP增长率": (-50.0, 50.0),
    "总人口": (1e4, np.inf),
    "贸易占GDP比重": (0.0, 500.0),
    "出口占GDP比重": (0.0, 300.0),
    "政府债务占GDP": (0.0, 500.0),
    "失业率": (0.0, 60.0),
    "GDP现价": (1e6, np.inf),
}


def find_indicator_file(code: str) -> str:
    """在 data/raw 下定位某个 WDI 指标代码对应的数据 CSV。"""
    for d in sorted(os.listdir(RAW)):
        full = os.path.join(RAW, d)
        if not os.path.isdir(full):
            continue
        if code in d:
            for f in os.listdir(full):
                if f.startswith("API_") and f.endswith(".csv"):
                    return os.path.join(full, f)
    raise FileNotFoundError(f"未找到指标 {code} 的原始文件")


def find_meta_file(code: str) -> str:
    for d in sorted(os.listdir(RAW)):
        full = os.path.join(RAW, d)
        if os.path.isdir(full) and code in d:
            for f in os.listdir(full):
                if f.startswith("Metadata_Country") and f.endswith(".csv"):
                    return os.path.join(full, f)
    raise FileNotFoundError(f"未找到指标 {code} 的国家元数据")


def load_country_meta() -> pd.DataFrame:
    """国家维表：编码、名称、所属区域、收入分组。取任一指标的元数据即可（同源同版本）。"""
    path = find_meta_file("NY.GDP.MKTP.CD")
    meta = pd.read_csv(path, encoding="utf-8-sig")
    meta = meta[["Country Code", "Region", "IncomeGroup", "TableName"]]
    meta = meta.rename(columns={
        "Country Code": "country_code",
        "Region": "region",
        "IncomeGroup": "income_group",
        "TableName": "country_name",
    })
    # 世界银行把区域聚合体（如"World""East Asia & Pacific"）的 Region 置空，
    # 据此可天然区分真实国家与聚合体，无需维护黑名单。
    meta["is_country"] = meta["region"].notna() & (meta["region"].astype(str).str.strip() != "")
    return meta.drop_duplicates("country_code")


def load_wide(code: str) -> pd.DataFrame:
    """读取一个指标的宽表 CSV（年份为列名），返回 country_code/year/value 长表。"""
    path = find_indicator_file(code)
    df = pd.read_csv(path, skiprows=4, encoding="utf-8-sig")
    df = df.dropna(subset=["Country Code"])
    year_cols = [c for c in df.columns if str(c).strip().isdigit()]
    long = df.melt(
        id_vars=["Country Code", "Country Name"],
        value_vars=year_cols,
        var_name="year",
        value_name="value",
    )
    long["year"] = pd.to_numeric(long["year"], errors="coerce")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.rename(columns={"Country Code": "country_code", "Country Name": "country_name"})
    long["indicator_code"] = code
    return long


def main() -> None:
    os.makedirs(CLEAN, exist_ok=True)
    io_log = {}

    # ---------- 1. 读取 + 国家维表对齐 ----------
    meta = load_country_meta()
    frames = []
    for code in INDICATORS:
        long = load_wide(code)
        io_log[code] = {"raw_rows": int(len(long))}
        frames.append(long)
    raw = pd.concat(frames, ignore_index=True)
    io_log["raw_total_rows"] = int(len(raw))

    # ---------- 2. 剔除国家聚合体，只保留真实国家 ----------
    before = len(raw)
    raw = raw.merge(meta[["country_code", "region", "income_group", "is_country"]],
                    on="country_code", how="left")
    raw = raw[raw["is_country"].fillna(False).astype(bool)].copy()
    io_log["dropped_aggregates_rows"] = int(before - len(raw))

    # ---------- 3. 年份裁剪 ----------
    before = len(raw)
    raw = raw[(raw["year"] >= YEAR_MIN) & (raw["year"] <= YEAR_MAX)]
    io_log["dropped_out_of_range_years"] = int(before - len(raw))

    # ---------- 4. 重复值 ----------
    before = len(raw)
    dup_mask = raw.duplicated(subset=["country_code", "year", "indicator_code"], keep="first")
    io_log["duplicate_rows_removed"] = int(dup_mask.sum())
    raw = raw[~dup_mask]

    # ---------- 5. 类型统一 ----------
    raw["year"] = raw["year"].astype(int)
    raw["indicator"] = raw["indicator_code"].map(lambda c: INDICATORS[c][0])
    raw["unit"] = raw["indicator_code"].map(lambda c: INDICATORS[c][1])

    # ---------- 6. 缺失盘点（区分"结构性缺失"与"真实缺失"）----------
    total_cells = len(raw)
    missing_cells = int(raw["value"].isna().sum())
    miss_by_ind = (raw.groupby("indicator")["value"]
                   .apply(lambda s: round(float(s.isna().mean()), 4))
                   .sort_values(ascending=False).to_dict())

    # ---------- 7. 异常值：规则型（硬阈值）+ 统计型（IQR 标记，仅记录不删除）----------
    raw["outlier_rule"] = False
    for ind, (lo, hi) in RULES.items():
        sel = raw["indicator"] == ind
        vals = raw.loc[sel, "value"]
        bad = sel & raw["value"].notna() & ((raw["value"] < lo) | (raw["value"] > hi))
        raw.loc[bad, "outlier_rule"] = True
        del vals

    raw["outlier_iqr"] = False
    for ind in INDICATORS.values():
        ind = ind[0]
        sel = raw["indicator"] == ind
        vals = raw.loc[sel, "value"].dropna()
        if len(vals) < 30:
            continue
        q1, q3 = vals.quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 3.0 * iqr, q3 + 3.0 * iqr  # 3 倍 IQR：极端离群，非普通离群
        raw.loc[sel & raw["value"].notna() & ((raw["value"] < lo) | (raw["value"] > hi)),
                "outlier_iqr"] = True

    io_log["outlier_rule_count"] = int(raw["outlier_rule"].sum())
    io_log["outlier_iqr_count"] = int(raw["outlier_iqr"].sum())

    # 规则型异常（业务上不可能）置为缺失；统计型离群（真实极端值如卢森堡人均 GDP）保留
    raw.loc[raw["outlier_rule"], "value"] = np.nan

    # ---------- 8. 派生指标 ----------
    wide = raw.pivot_table(index=["country_code", "country_name", "region", "income_group", "year"],
                           columns="indicator", values="value").reset_index()
    wide.columns.name = None

    wide = wide.sort_values(["country_code", "year"]).reset_index(drop=True)
    # 人均GDP 由 GDP现价 / 总人口 派生（世界银行官方人均 GDP 即此口径）
    wide["人均GDP"] = wide["GDP现价"] / wide["总人口"]
    g = wide.groupby("country_code", sort=False)
    # 同比：GDP 现价的年增长率（与官方不变价增长率互为校验）
    wide["GDP同比增速"] = g["GDP现价"].pct_change() * 100
    # 环比：相邻两年增长率之差，衡量增长动能变化（加速/减速）
    wide["增长动能变化"] = g["GDP增长率"].diff()
    wide["人均GDP同比"] = g["人均GDP"].pct_change() * 100
    wide["ln_GDP"] = np.log(wide["GDP现价"].where(wide["GDP现价"] > 0))

    # 全球份额（同一年度内，占全部样本国家合计的比重）
    year_total = wide.groupby("year")["GDP现价"].transform("sum")
    wide["全球GDP份额"] = wide["GDP现价"] / year_total * 100
    # 区域份额
    reg_total = wide.groupby(["year", "region"])["GDP现价"].transform("sum")
    wide["区域GDP份额"] = wide["GDP现价"] / reg_total * 100

    # ---------- 9. 导出 ----------
    master = raw[["country_code", "country_name", "region", "income_group",
                  "year", "indicator_code", "indicator", "unit",
                  "value", "outlier_iqr"]].sort_values(
        ["country_code", "year", "indicator_code"]).reset_index(drop=True)
    master.to_csv(os.path.join(CLEAN, "master.csv"), index=False, encoding="utf-8-sig")

    wide.to_csv(os.path.join(CLEAN, "country_year.csv"), index=False, encoding="utf-8-sig")

    gdp = wide.pivot_table(index=["country_code", "country_name", "region", "income_group"],
                           columns="year", values="GDP现价").reset_index()
    gdp.columns.name = None
    gdp.to_csv(os.path.join(CLEAN, "gdp_wide.csv"), index=False, encoding="utf-8-sig")

    dict_rows = [{
        "字段名": "country_code", "类型": "string", "说明": "ISO3 国家代码（主键之一）",
        "来源": "WDI 元数据",
    }, {
        "字段名": "year", "类型": "int", "说明": f"年份，{YEAR_MIN}-{YEAR_MAX}（主键之一）",
        "来源": "WDI 宽表列名",
    }, {
        "字段名": "region", "类型": "string", "说明": "世界银行七大区域",
        "来源": "WDI Metadata_Country",
    }, {
        "字段名": "income_group", "类型": "string",
        "说明": "收入分组：High/Low/Lower middle/Upper middle income",
        "来源": "WDI Metadata_Country",
    }]
    for code, (name, unit, meaning) in INDICATORS.items():
        dict_rows.append({
            "字段名": name, "类型": "float", "说明": f"{meaning}（单位：{unit}）",
            "来源": f"WDI {code}",
        })
    for name, note in [
        ("GDP同比增速", "由 GDP现价 逐年 pct_change 派生，%"),
        ("增长动能变化", "当年 GDP增长率 与上年之差，百分点"),
        ("人均GDP同比", "由 人均GDP 逐年 pct_change 派生，%"),
        ("ln_GDP", "GDP现价 的自然对数，用于压缩量纲"),
        ("全球GDP份额", "该国 GDP 占当年样本国家合计的比重，%"),
        ("区域GDP份额", "该国 GDP 占当年所属区域合计的比重，%"),
        ("人均GDP", "GDP现价 / 总人口，现价美元（本脚本派生）"),
        ("outlier_iqr", "是否被 3×IQR 判为极端离群（保留，不删除）"),
    ]:
        dict_rows.append({"字段名": name, "类型": "float/派生", "说明": note, "来源": "本脚本派生"})
    pd.DataFrame(dict_rows).to_csv(os.path.join(CLEAN, "data_dictionary.csv"),
                                   index=False, encoding="utf-8-sig")

    report = {
        "indicators": {k: v[0] for k, v in INDICATORS.items()},
        "year_range": [YEAR_MIN, YEAR_MAX],
        "country_count": int(wide["country_code"].nunique()),
        "country_year_rows": int(len(wide)),
        "master_long_rows": int(len(master)),
        "missing_rate_overall": round(missing_cells / total_cells, 4),
        "missing_rate_by_indicator": miss_by_ind,
        "io_log": io_log,
        "region_counts": wide.drop_duplicates("country_code")["region"].value_counts().to_dict(),
        "income_counts": wide.drop_duplicates("country_code")["income_group"].value_counts().to_dict(),
    }
    with open(os.path.join(CLEAN, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[01] 主表 长表 {len(master):,} 行 | 宽表 {len(wide):,} 行 | "
          f"国家 {report['country_count']} 个 | 缺失率 {report['missing_rate_overall']:.2%}")
    print(f"[01] 输出目录：{CLEAN}")


if __name__ == "__main__":
    main()
