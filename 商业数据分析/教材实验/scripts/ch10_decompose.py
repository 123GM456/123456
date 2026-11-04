"""第 10 章 使用效应分解方法做预报 · 乘法分解（手写版）

教材原做法
----------
第 10 章（`效应分解法.pbix`）把时间序列拆成三块：

    Y = T × S × I        T 趋势项、S 季节项、I 不规则项

Power BI / WPS 里这套是点几下「预测」自动算的；教材同时给了「报表」和「预测」两个页面。
配套数据：`AirPassengers`（1949-01 至 1960-12 的月度航空客运量，共 144 个月）。

迁移思路
--------
本机没有 statsmodels（`seasonal_decompose` 就在里面），也没有 scipy，
所以这里**按教材公式手写**整套分解，反而把每一步口径讲清楚了：

1. 趋势项 T：12 期中心化移动平均（偶数期要做 2×12 再平均，否则会错半期）
2. 季节项 S：去趋势后 y/T 按月份取平均，再归一化到「均值 = 1」
3. 不规则项 I：y / (T × S)
4. 预报：把 T 线性外推 + 乘回对应月份的季节指数

运行：python scripts/ch10_decompose.py
输出：outputs/ch10_*.csv、outputs/ch10_decompose.png
"""
from __future__ import annotations

import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ch10")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
C_MAIN, C_ALT, C_GREEN, C_GRAY = "#4472C4", "#ED7D31", "#70AD47", "#A5A5A5"
GRID = "#E1E4E8"
PERIOD = 12


def centered_ma(y: pd.Series, period: int = PERIOD) -> pd.Series:
    """12 期中心化移动平均：先做 2×12 滑动，使结果对齐到月中。"""
    ma = y.rolling(period, center=True).mean()
    # 偶数期：简单中心化平均会落在两期之间，教材用的是 2×12 的加权平均
    ma = y.rolling(period, center=True).mean().rolling(2).mean()
    return ma


def decompose(y: pd.Series) -> pd.DataFrame:
    """乘法分解：Y = T × S × I。"""
    df = pd.DataFrame({"y": y})
    df["trend"] = centered_ma(df["y"])
    df["detrended"] = df["y"] / df["trend"]

    # 季节指数：同一月份取平均，再除以整体均值归一化（保证 12 个月平均为 1）
    month = df.index.month
    raw = df.groupby(month)["detrended"].mean()
    seasonal_idx = raw / raw.mean()

    df["seasonal"] = [seasonal_idx[m] for m in month]
    df["sa"] = df["y"] / df["seasonal"]      # 季节调整后序列
    df["resid"] = df["y"] / (df["trend"] * df["seasonal"])
    return df, seasonal_idx


def forecast(df: pd.DataFrame, seasonal_idx: pd.Series, horizon: int = 12) -> pd.DataFrame:
    """预报 = 趋势外推 × 季节指数。趋势用最后 36 个月拟合的线性回归外推。"""
    tail = df["trend"].dropna().tail(36)
    x = np.arange(len(tail))
    if len(tail) < 2:                      # 数据不足时退化为常数趋势
        slope, intercept = 0.0, float(df["trend"].dropna().iloc[-1])
    else:
        slope, intercept = np.polyfit(x, tail.values, 1)
    trend_fore = intercept + slope * np.arange(len(tail), len(tail) + horizon)

    last = df.index[-1]
    future_idx = pd.date_range(last + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    seasonal = np.array([seasonal_idx[i.month] for i in future_idx])
    out = pd.DataFrame({
        "month": future_idx,
        "trend": trend_fore,
        "seasonal": seasonal,
        "forecast": trend_fore * seasonal,
    })
    resid_std = float(df["resid"].std())
    out["lo95"] = out["forecast"] * (1 - 1.96 * resid_std)
    out["hi95"] = out["forecast"] * (1 + 1.96 * resid_std)
    num = out.select_dtypes("number").columns.drop("seasonal")
    out[num] = out[num].round(1)
    out["seasonal"] = out["seasonal"].round(3)
    return out


def holiday_case() -> pd.DataFrame:
    """教材里的第二个案例：3 月信用卡消费额的「节日效应」。

    注意量纲：`信用卡消费额_含节日.xlsx` 的单位是「元」（单日百万级），
    `信用卡消费额_去除节日.xlsx` 的单位与之不同（单日百级，约为前者的 1/9167）。
    因此两者不能直接相减，这里统一换算成「相对指数（均值 = 100）」再比较形态，
    这也是处理量纲不一致数据时的标准做法。
    """
    with_h = pd.read_csv(os.path.join(DATA, "card_holiday.csv"))
    without = pd.read_csv(os.path.join(DATA, "card_noholiday.csv"))
    with_h["date"] = pd.to_datetime(with_h["date"])
    without["date"] = pd.to_datetime(without["date"])

    m = with_h.merge(without, on="date", suffixes=("_含节日", "_剔除节日"))
    m["指数_含节日"] = (m["amount_含节日"] / m["amount_含节日"].mean() * 100).round(2)
    m["指数_剔除节日"] = (m["amount_剔除节日"] / m["amount_剔除节日"].mean() * 100).round(2)
    m["指数差"] = (m["指数_含节日"] - m["指数_剔除节日"]).round(2)

    top = m.loc[m["指数差"].abs().nlargest(3).index]
    print("\n[案例 2] 信用卡消费额的节日效应（2013 年 3 月，31 天）")
    print(f"    含节日合计 {m['amount_含节日'].sum():,.0f}（元）；"
          f"剔除节日合计 {m['amount_剔除节日'].sum():,.1f}（另一量纲）")
    r = m["amount_含节日"].corr(m["amount_剔除节日"])
    print(f"    两序列日级相关系数 r = {r:.4f}——「剔除节日」是平滑基线，不跟随日级噪声，")
    print("    所以两者不能逐日相减，只能比「相对指数」的偏离。")
    print("    偏离基线最大的 3 天（相对指数差，单位：百分点）：")
    for _, r in top.iterrows():
        print(f"      {r['date']:%Y-%m-%d}  含节日 {r['指数_含节日']:.1f}，"
              f"剔除节日 {r['指数_剔除节日']:.1f}，差 {r['指数差']:+.1f}")
    print("    说明：这份数据只有 31 天（1 个周期），做不了 12 期分解，"
          "因此只用来演示「节日效应」这一种季节成分；\n"
          "    真正的季节分解用 AirPassengers 的 144 个月。")
    return m


def plot(df: pd.DataFrame, seasonal_idx: pd.Series, fc: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), dpi=150,
                             gridspec_kw={"height_ratios": [2, 1.1, 1.3]})

    a = axes[0]
    a.plot(df.index, df["y"], color=C_MAIN, lw=1.3, label="原始序列")
    a.plot(df.index, df["trend"], color=C_ALT, lw=1.8, label="趋势项 T（12 期中心化 MA）")
    a.plot(df.index, df["sa"], color=C_GREEN, lw=1.0, alpha=0.85, label="季节调整后 T×I")
    a.plot(fc["month"], fc["forecast"], color="#C00000", lw=1.8, ls="--",
           label="预报 T×S")
    a.fill_between(fc["month"], fc["lo95"], fc["hi95"], color="#C00000", alpha=0.10,
                   label="95% 置信区间")
    a.set_title("航空客运量的乘法分解与 12 期预报", fontsize=12)
    a.set_ylabel("客运量（千人）")
    a.legend(fontsize=8.5, ncol=2)
    a.grid(color=GRID)
    a.set_axisbelow(True)

    a = axes[1]
    months = np.arange(1, 13)
    a.bar(months, seasonal_idx.values, color=C_GREEN, width=0.62)
    a.axhline(1.0, color=C_GRAY, lw=1, ls="--")
    for m, v in zip(months, seasonal_idx.values):
        a.text(m, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    a.set_xticks(months)
    a.set_xticklabels([f"{m}月" for m in months])
    a.set_title("季节指数 S（12 个月平均 = 1，>1 表示旺季）", fontsize=10.5)
    a.set_ylim(0, seasonal_idx.max() * 1.18)
    a.grid(axis="y", color=GRID)
    a.set_axisbelow(True)

    a = axes[2]
    a.plot(df.index, df["resid"], color=C_GRAY, lw=1.0)
    a.axhline(1.0, color=C_GRAY, lw=1, ls="--")
    a.set_title(f"不规则项 I（标准差 {df['resid'].std():.4f}）", fontsize=10.5)
    a.set_ylabel("I")
    a.grid(color=GRID)
    a.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(OUT, "ch10_decompose.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\n图 → {os.path.relpath(path, ROOT)}")


def main() -> int:
    print("=" * 78)
    print("第 10 章 · 效应分解法（Y = T × S × I）")
    print("=" * 78)

    air = pd.read_csv(os.path.join(DATA, "air.csv"))
    air["date"] = pd.to_datetime(air["date"])
    y = air.set_index("date")["passengers"].astype(float)
    y.index = pd.DatetimeIndex(y.index, freq="MS")
    print(f"\n[案例 1] AirPassengers：{len(y)} 个月（{y.index[0]:%Y-%m} → {y.index[-1]:%Y-%m}）")

    df, seasonal_idx = decompose(y)
    print(f"    趋势项可用 {df['trend'].notna().sum()} 个月（两端各损失"
          f" {PERIOD // 2 + 1} 个月，这是移动平均的代价）")
    print(f"    季节指数：旺季 {seasonal_idx.idxmax()} 月（{seasonal_idx.max():.3f}），"
          f"淡季 {seasonal_idx.idxmin()} 月（{seasonal_idx.min():.3f}），"
          f"峰谷比 {seasonal_idx.max() / seasonal_idx.min():.2f}")

    fc = forecast(df, seasonal_idx, horizon=12)
    print(f"\n    12 期预报（{fc['month'].iloc[0]:%Y-%m} → {fc['month'].iloc[-1]:%Y-%m}）：")
    print(fc[["month", "trend", "seasonal", "forecast", "lo95", "hi95"]]
          .assign(month=lambda d: d["month"].dt.strftime("%Y-%m")).to_string(index=False))

    # 回测：用 1949-01 至 1959-12 训练，预测 1960 年 12 个月
    train = y[y.index < "1960-01-01"]
    dtr, sidx = decompose(train)
    fbt = forecast(dtr, sidx, horizon=12)
    actual = y[y.index >= "1960-01-01"].values
    mape = float(np.mean(np.abs((actual - fbt["forecast"].values) / actual)) * 100)
    rmse = float(np.sqrt(np.mean((actual - fbt["forecast"].values) ** 2)))
    print(f"\n    回测（训练至 1959-12，预测 1960 全年）：MAPE {mape:.2f}%，"
          f"RMSE {rmse:.2f} 千人")

    holiday_case()
    plot(df, seasonal_idx, fc)

    out = df.reset_index().rename(columns={"date": "month"})
    out.to_csv(os.path.join(OUT, "ch10_decompose.csv"), index=False, encoding="utf-8-sig")
    seasonal_idx.rename("季节指数").to_frame().reset_index(names="月份").to_csv(
        os.path.join(OUT, "ch10_seasonal.csv"), index=False, encoding="utf-8-sig")
    fc.to_csv(os.path.join(OUT, "ch10_forecast.csv"), index=False, encoding="utf-8-sig")
    for f in ("ch10_decompose.csv", "ch10_seasonal.csv", "ch10_forecast.csv"):
        print(f"  → outputs/{f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
