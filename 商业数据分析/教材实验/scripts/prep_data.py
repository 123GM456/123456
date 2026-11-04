"""教材实验 · 数据准备：把教材自带的 xlsx / GBK csv 统一转成 UTF-8 的 csv。

为什么单独有这一步
------------------
教材原始素材混着三种编码与格式：xlsx 工作簿（带标题行、说明列、参考答案）、
GBK 编码的 csv、只有数据没有表头的 csv。直接在每个实验脚本里读原始文件会导致
脚本里全是 `skiprows=2, usecols=[1, 2]` 这种"魔法参数"，无法阅读。
所以先做一次可复现的抽取，把"教材文件的物理布局"和"分析逻辑"解耦：
    data/ 下的每个 csv 都是干净的、UTF-8、带表头的二维表，
    脚本只依赖 data/，换个教材版本只需改这个文件。

依赖：pandas + openpyxl（只有本脚本需要 openpyxl）。
运行：python scripts/prep_data.py
输出：data/ch01 … data/ch10
"""
from __future__ import annotations

import os
import shutil
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
BOOK = "1《CDA 一级认证教材：商业数据分析》"


def find_textbook() -> str:
    """定位教材目录：环境变量 CDA_TEXTBOOK 优先，否则按常见位置探测。"""
    env = os.environ.get("CDA_TEXTBOOK")
    if env and os.path.isdir(env):
        return env
    candidates = [
        os.path.join(os.path.dirname(ROOT), BOOK),
        os.path.join(os.path.dirname(ROOT), "1", BOOK),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ROOT))),
                     "商业数据分析", "1", BOOK),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return candidates[0]


TEXTBOOK = find_textbook()

CH1 = os.path.join(TEXTBOOK, "第1章 数据分析思维",
                   "关系模型演示-不建议用poweBI操作关系型数据模型")
CH2 = os.path.join(TEXTBOOK, "第2章 数据分析方法")
CH5 = os.path.join(TEXTBOOK, "第5章 业务数据分析", "第5章  PowerBI业务看板案例-银行案例")
CH10 = os.path.join(TEXTBOOK, "第10章 使用效应分解方法做预报")

# 第 1 章的 8 张表就是经典的 PKDD'99 捷克银行数据集，学科里通常叫 Kdd99
CH1_TABLES = ["clients", "accounts", "disp", "card", "loans", "order", "trans", "district"]

# district.csv 的列名被教材匿名成了 A1/GPB/A4…，按 PKDD'99 官方数据字典还原
DISTRICT_COLS = {
    "A1": "district_id", "GDP": "avg_salary", "A4": "population",
    "A10": "n_cities", "A11": "urban_ratio", "A12": "unemp_95",
    "A13": "unemp_96", "a16": "crime_96", "A14": "n_ent", "A15": "crime_95",
}


def ensure_dir(*parts: str) -> str:
    path = os.path.join(DATA, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def save(df: pd.DataFrame, *parts: str) -> None:
    path = os.path.join(ensure_dir(*parts[:-1]), parts[-1])
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  OK {os.path.relpath(path, ROOT):<44} {df.shape[0]:>6} 行 × {df.shape[1]} 列")


def read_xlsx(path: str, sheet: str, **kw) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet, **kw)


# --------------------------------------------------------------------------- #
# 第 1 章：关系模型 8 张表（GBK csv）+ 维度模型用的商场销售数据
# --------------------------------------------------------------------------- #
def prep_ch01() -> None:
    print("[ch01] 关系模型 8 表 + 商场销售")
    for name in CH1_TABLES:
        df = pd.read_csv(os.path.join(CH1, f"{name}.csv"), encoding="gb18030")
        if name == "district":
            df = df.rename(columns=DISTRICT_COLS)
        save(df, "ch01", f"{name}.csv")
    sale = pd.read_csv(os.path.join(TEXTBOOK, "第1章 数据分析思维", "sale.csv"),
                       encoding="gb18030")
    save(sale, "ch01", "sale.csv")


# --------------------------------------------------------------------------- #
# 第 2 章：6 个基础分析范式 + 5 类引申方法 + Excel 函数练习
# --------------------------------------------------------------------------- #
def prep_ch02() -> None:
    print("[ch02] 分析范式 / 引申方法 / Excel 函数练习")
    base = os.path.join(CH2, "1、分析的基础范式")
    ans = os.path.join(base, "data-有答案")
    raw = os.path.join(base, "data-无答案")

    # 1-1 波士顿矩阵：订单明细（品牌 × 规格 × 单价 × 销量）
    boston = read_xlsx(os.path.join(ans, "1-1波士顿矩阵-参考.xlsx"), "销售表")
    boston.columns = ["order_id", "sale_date", "brand", "spec", "price",
                      "qty", "amount"]
    save(boston, "ch02", "boston_sales.csv")

    # 1-2 RFM：2019 年母婴零售流水 + 教材参考答案
    rfm = read_xlsx(os.path.join(ans, "1-2RFM模型-参考.xlsx"), "原始数据")
    rfm = rfm.iloc[:, :8]
    rfm.columns = ["flow_id", "user_id", "cat1", "cat2", "product",
                   "join_date", "sale_date", "amount"]
    save(rfm.dropna(subset=["user_id"]), "ch02", "rfm_orders.csv")

    rfm_ans = read_xlsx(os.path.join(ans, "1-2RFM模型-参考.xlsx"), "参考答案",
                        skiprows=5, usecols=range(9))
    rfm_ans.columns = ["user_id", "last_buy", "freq", "monetary",
                       "recency_days", "r_score", "f_score", "m_score",
                       "user_type"]
    save(rfm_ans.dropna(subset=["user_id"]), "ch02", "rfm_answer.csv")

    # 1-3 用户忠诚度：销售流水表
    loy = read_xlsx(os.path.join(ans, "1-3用户忠诚度模型-参考.xlsx"), "销售流水表")
    loy = loy.dropna(how="all", axis=1)
    save(loy, "ch02", "loyalty_flow.csv")

    # 1-4 同期群：用户注册日期 + 登录明细
    coh = read_xlsx(os.path.join(ans, "1-4同期群分析-参考.xlsx"), "用户登录明细",
                    usecols=range(5))
    coh.columns = ["user_id", "reg_date", "login_time", "login_date", "day_label"]
    save(coh.dropna(subset=["user_id"]), "ch02", "cohort_logins.csv")

    # 2-1 漏斗图：浏览→收藏→加购→购买
    funnel_raw = read_xlsx(os.path.join(raw, "2-1漏斗图.xlsx"), "练习", header=None)
    fun = funnel_raw.iloc[2:6, 1:3].dropna()
    fun.columns = ["behavior", "users"]
    save(fun, "ch02", "funnel.csv")
    aarrr = funnel_raw.iloc[10:15, 1:3].dropna()
    aarrr.columns = ["stage", "users"]
    save(aarrr, "ch02", "funnel_aarrr.csv")

    # 3-1 相关分析：投入成本 vs 产出收益
    corr = read_xlsx(os.path.join(raw, "3-1相关分析.xlsx"), "原始数据")
    corr.columns = ["revenue", "cost"]
    save(corr.dropna(), "ch02", "corr.csv")

    # 引申方法：趋势 / 构成 / 分布 / 关系（在另一个一级小节下）
    ext_raw = os.path.join(CH2, "2、由基础分析范式引申出的分析方法", "data-无答案")
    # 一张 sheet 里竖着排了三张表，必须按行区间切，不能整表 skiprows
    trend_raw = read_xlsx(os.path.join(ext_raw, "1趋势分析.xlsx"), "趋势图",
                          header=None)
    trend = trend_raw.iloc[2:13, 1:3].dropna()
    trend.columns = ["year", "orders"]
    save(trend, "ch02", "trend.csv")

    week = trend_raw.iloc[18:29, 1:5].dropna()
    week.columns = ["week", "avg_hours", "mean_hours", "alert"]
    save(week, "ch02", "trend_week.csv")

    month = trend_raw.iloc[35:47, 1:4].dropna(subset=[1, 2])
    month.columns = ["month", "orders", "mom_pct"]
    save(month, "ch02", "trend_month.csv")

    comp_raw = read_xlsx(os.path.join(ext_raw, "3构成分析.xlsx"), "构成分析",
                         header=None)
    comp = comp_raw.iloc[4:8, 1:3].dropna()
    comp.columns = ["product", "qty"]
    save(comp, "ch02", "compose.csv")

    comp_year = comp_raw.iloc[17:22, 1:4].dropna()
    comp_year.columns = ["year", "产品 1", "产品 2", "产品 3"]
    save(comp_year, "ch02", "compose_year.csv")

    dist = read_xlsx(os.path.join(ext_raw, "4分布分析.xlsx"), "分布分析")
    traffic = dist.iloc[2:, [1, 2]].dropna()
    traffic.columns = ["ts", "traffic"]
    save(traffic, "ch02", "dist_traffic.csv")
    age = dist.iloc[2:, [10, 11]].dropna()
    age.columns = ["user_id", "age"]
    save(age, "ch02", "dist_age.csv")

    rel = read_xlsx(os.path.join(ext_raw, "5关系分析.xlsx"), "关系图", usecols=[24, 25])
    rel.columns = ["revenue", "cost"]
    save(rel.dropna(), "ch02", "relation.csv")

    # Excel 函数练习：IF+AND+OR / VLOOKUP / COUNTIF / SUMIF
    excel = os.path.join(CH2, "4、EXCEL基础操作")
    ifx = read_xlsx(os.path.join(excel, "1、电子表格常用函数（WPS和EXCEL）.xlsx"),
                    "1IF+AND+OR例子")
    save(ifx.dropna(how="all"), "ch02", "excel_if.csv")

    cnt = read_xlsx(os.path.join(excel, "1、电子表格常用函数（WPS和EXCEL）.xlsx"),
                    "3COUNTIF-统计")
    save(cnt.dropna(how="all"), "ch02", "excel_countif.csv")

    sm = read_xlsx(os.path.join(excel, "1、电子表格常用函数（WPS和EXCEL）.xlsx"),
                   "4借贷-sumif")
    save(sm.dropna(how="all"), "ch02", "excel_sumif.csv")

    vlook = read_xlsx(os.path.join(excel, "2、电子表格查找引用函数（WPS和EXCEL）.xlsx"),
                      "1.VLOOKUP精确查找")
    left = vlook.iloc[:, 0:5]
    left.columns = ["item_code", "item_name", "date", "qty", "amount"]
    save(left.dropna(subset=["item_code"]), "ch02", "excel_vlookup.csv")
    right = vlook.iloc[:, 6:8].dropna()
    right.columns = ["item_code", "item_name"]
    save(right, "ch02", "excel_vlookup_map.csv")


# --------------------------------------------------------------------------- #
# 第 5 章：银行理财销售 + 三张维度说明表
# --------------------------------------------------------------------------- #
def prep_ch05() -> None:
    print("[ch05] 银行理财销售 + 维度表")
    path = os.path.join(CH5, "银行案例数据 - 学员用.xlsx")
    sales = read_xlsx(path, "销售数据")
    sales.columns = ["risk_code", "purpose", "income", "cat_code", "age_band",
                     "gender", "reason", "edu_code", "amount", "term", "profit"]
    save(sales, "ch05", "bank_sales.csv")
    for sheet, fname, cols in [("风险偏好说明表", "bank_risk.csv", ["risk_code", "risk_desc"]),
                               ("品类说明表", "bank_category.csv", ["cat_code", "cat_name"]),
                               ("学历说明表", "bank_edu.csv", ["edu_code", "edu_name"])]:
        df = read_xlsx(path, sheet)
        df.columns = cols
        save(df.dropna(), "ch05", fname)


# --------------------------------------------------------------------------- #
# 第 10 章：时间序列（月度航空客流 + 每日信用卡消费额，含/去节日两版）
# --------------------------------------------------------------------------- #
def prep_ch10() -> None:
    print("[ch10] 时间序列")
    air = pd.read_csv(os.path.join(CH10, "AirPassengers.csv"))
    air.columns = ["date", "passengers", "ln_passengers"]
    air["date"] = pd.to_datetime(air["date"], format="%m/%d/%Y")
    save(air[["date", "passengers"]], "ch10", "air.csv")

    for src, out in [("信用卡消费额_含节日.xlsx", "card_holiday.csv"),
                     ("信用卡消费额_去除节日.xlsx", "card_noholiday.csv")]:
        sheet = "pos" if src.endswith("含节日.xlsx") else "Sheet1"
        df = read_xlsx(os.path.join(CH10, src), sheet)
        df = df.iloc[:, :2]
        df.columns = ["date", "amount"]
        df["date"] = pd.to_datetime(df["date"])
        save(df.dropna(), "ch10", out)


def main() -> int:
    if not os.path.isdir(TEXTBOOK):
        print(f"找不到教材目录：{TEXTBOOK}")
        return 1
    print(f"教材目录：{TEXTBOOK}\n输出目录：{DATA}\n")
    prep_ch01()
    prep_ch02()
    prep_ch05()
    prep_ch10()
    # 第 8 章 SQL 练习重新使用第 1 章的 8 张表，不重复存一份
    print("\n完成。data/ch01 同时供第 8 章（sqlite3）与第 9 章（用户画像）使用。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
