# 《商业数据分析》教材实验：Excel / Power BI → Python 迁移

本目录是《CDA 一级认证教材：商业数据分析》配套实验的 **Python 复刻版**。
教材里的分析原本分散在 **Excel 公式、Excel 数据透视、Power BI 报表和 SQL** 里，
这里把每一个案例都改写成可独立运行的 `.py`，并把「教材怎么点」与「代码怎么写」逐条对照。

- 教材目录：`../1《CDA 一级认证教材：商业数据分析》`（原始 xlsx / pbix / sql，不入库）
- 代码：`scripts/*.py`，一个脚本对应教材一章
- 结果：`outputs/*.csv`（中间结果）与 `outputs/*.png`、`outputs/ch02_dashboard.html`（图表）

---

## 一、三条作业要求的落地方式

| 要求 | 本仓库怎么做的 |
| --- | --- |
| 1. Power BI / Excel 实现的，理解内涵并迁移成 Python | 第 1、2、5、9、10 章的 Excel 公式、数据透视、Power BI 报表全部重写为 pandas / pyecharts，见下方「技术映射表」 |
| 2. 本身就是 Python（ipynb）的，形成 `.py` 并理解代码 | 教材内 **0 个 `.ipynb`**（实测扩展名统计：`.pbix` 92、`.pbiviz` 133、`.csv` 64、`.xlsx` 62、`.pdf` 25、`.sql` 7），故此项无对应文件；SQL 类放第 8 章用 `sqlite3` 执行 |
| 3. 实验内容上传到 GitHub / Gitee | 位于仓库 `商业数据分析/教材实验/`，随主仓库一起提交 |

92 个 `.pbix` 里有 **81 个是「图表安装文件」**（外部视觉对象安装包，只有样式没有分析逻辑，不迁移），
真正含案例的 11 个已在下方章节表里逐一对上。

---

## 二、章节对照：教材做法 → Python 脚本

| 章 | 教材做法 | Python 文件 | 主要产出 |
| --- | --- | --- | --- |
| 1 | Power BI 星型模型（KDD99 银行数据 8 张表） | `ch01_data_model.py` | 关系图 + 4 张汇总表；事实表 1 056 320 行，展开后 1 262 625 行 × 33 列 |
| 2 | Excel：IF/VLOOKUP/COUNTIF/SUMIF/透视表 | `ch02_excel2pandas.py` | 5 个公式对照案例，11 名学生评级、100 行 VLOOKUP、13 条传票汇总 |
| 2 | Power BI：波士顿矩阵、RFM、忠诚度、同期群、漏斗、相关 | `ch02_six_methods.py` | 7 张 PNG + 6 个 csv；RFM 与教材答案比对 R 100% / M 100% |
| 2 | Power BI 报表页 | `ch02_dashboard.py` | `ch02_dashboard.html`，5 个联动图表 |
| 5 | Power BI 银行销售 KPI 看板 | `ch05_bank_kpi.py` | 440 笔成交的 KPI、风险等级、收入段、年龄段、购买目的 |
| 8 | MySQL 教材语句（`kdd99` 库） | `ch08_sql_practice.py` | `kdd99.db` + 10 条语句结果 + pandas 等价写法对照 |
| 9 | Power BI as-of 连接做用户画像 | `ch09_user_profile.py` | 892 张卡的画像标签与 4 面板图 |
| 10 | WPS「AI 预测」/ 效应分解 | `ch10_decompose.py` | AirPassengers 乘法分解 + 12 期预报（MAPE 9.56%） |
| — | 数据抽取（把教材物理目录摊平成 csv） | `prep_data.py` | `data/ch01..ch10` 全部 UTF-8 csv |

> 教材没有第 4、6 章；第 3、7、11–13 章只有 PDF 白皮书与模板 xlsx，没有可运行的分析过程，
> 因此不单独出脚本（对应方法论已分别落在第 2、5、9、10 章的实现里）。

---

## 三、技术映射表（这是本作业最值钱的部分）

| 教材里的操作 | Python 等价写法 | 出现在 |
| --- | --- | --- |
| `VLOOKUP` / `XLOOKUP` | `pd.merge(df, map_df, on="编码", how="left")` | `ch02_excel2pandas.py` |
| `SUMIF` / `SUMIFS` | `df.groupby("科目")["金额"].sum()` / `pivot_table(index=..., columns=...)` | 同上 |
| `COUNTIF` / `COUNTIFS` | `mask.sum()`、`df[mask].groupby(...).size()` | 同上 |
| `IF` / `AND` / `OR` | `np.where`、`np.select([c1, c2], [v1, v2], default)` | 同上 |
| `IFERROR` | `pd.to_numeric(..., errors="coerce")`、`fillna` | 同上 |
| Excel 数据透视表 | `pd.pivot_table(index, columns, values, aggfunc)` | 同上 |
| Power BI 关系模型（一对多） | 多表 `merge` 成星型 / 雪花模型 | `ch01_data_model.py` |
| Power BI 度量值 + 筛选上下文 | 布尔索引 `mask` → `.loc[mask, col].sum()` | `ch05_bank_kpi.py` |
| 切片器联动 | 把筛选条件做成函数参数，各自出图 | `ch02_dashboard.py`、`ch05_bank_kpi.py` |
| Power BI 可视化对象 / 自定义视觉 | `pyecharts`（交互）与 `matplotlib`（静态） | 全部 |
| 波士顿矩阵（象限图） | 按分界值 `np.where` 打标签 + `scatter(size=...)` | `ch02_six_methods.py` |
| RFM 打分 | `pd.qcut` / `pd.cut` 分箱后拼类别 | 同上 |
| 同期群留存 | `groupby("注册月")` + 按 `day_label` 统计累计留存 | 同上 |
| `as-of` 连接（取发卡前最后一笔交易） | `df[df["date"] < df["issued"]].groupby("card_id").agg(...)` | `ch09_user_profile.py` |
| SQL 开窗 `rank() over` | `df.groupby(...)[col].rank(ascending=False)` 或 `sqlite3` 直接跑 | `ch08_sql_practice.py` |
| WPS「AI 预测」/ 乘法分解 | 手写中心化移动平均 + 季节指数（无 statsmodels 依赖） | `ch10_decompose.py` |

---

## 四、运行方式

```bash
# 1) 依赖（只用 pandas / numpy / pyecharts / matplotlib）
pip install -r requirements.txt

# 2) 一次性抽数：把教材 xlsx / GBK csv 摊平成 UTF-8 csv
#    教材目录不在默认位置时用环境变量指定
set CDA_TEXTBOOK=D:\path\to\1《CDA 一级认证教材：商业数据分析》
python scripts/prep_data.py

# 3) 逐章运行（也可一键全跑）
python scripts/ch01_data_model.py
python scripts/ch02_excel2pandas.py
python scripts/ch02_six_methods.py
python scripts/ch02_dashboard.py
python scripts/ch05_bank_kpi.py
python scripts/ch08_sql_practice.py
python scripts/ch09_user_profile.py
python scripts/ch10_decompose.py

python run_all.py          # 依次跑 2) 与 3) 的全部步骤
python scripts/build_index.py   # 生成 outputs/index.html（图 + 结果文件总览页）
```

产物都在 `outputs/`；看板 `outputs/ch02_dashboard.html` 直接双击即可打开（本地 echarts，无需联网）。

> 注：本机 PATH 里的默认 `python` 可能是不带 pandas 的版本，
> 建议用 `py -3.13` 或写全解释器路径执行。

---

## 五、几个必须说明的口径问题

1. **波士顿矩阵的纵轴换成了环比**：教材数据只覆盖 2021-07-01～2021-08-31 两个月，
   算不出「年复合增长率」，强行外推会得到假数据，所以纵轴改为「8 月对 7 月环比增速」，
   并在脚本里写明了这个取舍。
2. **RFM 的观测日是 2019-08-03**：这个日期不是数据最后一天，而是从教材答案的
   `recency_days` 反推出来的（用户 641397 最后购买 2019-04-26 → 答案给 99 天）。
   用「数据最后一天 + 1」会让整列 R 偏 10 天，评分全错位。
3. **`freq` 用「有消费的天数」而不是流水条数**：与教材答案吻合率 74.99%；
   剩余差异来自教材答案基于更宽的订单表，属于数据口径差异，已在脚本注释里写明。
   比对结果：recency 100%、monetary 100%。
4. **同期群留存要分清「窗口」和「每日」两个口径**。教材矩阵的 D0/D1/D3/D7/D14/D30
   是**窗口留存**：D3 指注册后第 2—3 天这个窗口内至少登录过一次的人占比，D14 指第 8—14 天。
   窗口长度不同，数字自然忽高忽低（D3 86.7% > D1 61.6%），不是算错。
   按这个口径复算，六格与教材值**偏差 0.00 个百分点**，可以确认口径完全对齐；
   真正用来看衰减的是**每日留存**（第 N 天当天有登录的人占比），这条曲线才单调下降：
   次日 61.6% → 第 7 日 48.9% → 第 14 日 26.0% → 第 30 日 0.1%。
5. **KDD99 的 `idle_days` 全部落在 1–27 天**：发卡日紧贴账户首笔交易，按天数分箱只有一个档位，
   所以「活跃度」改用「发卡前交易笔数」的四分位。
6. **信用卡节日案例两表量纲不同**：含节日表单位是元，剔除节日表约为它的 1/9167，
   两者不能逐日相减，只能换算成「相对指数（均值=100）」比较，脚本里已注明。

---

## 六、数据体积与入库策略

| 路径 | 体积 | 是否入库 | 说明 |
| --- | --- | --- | --- |
| `data/ch01/trans.csv` | 65 MB | ❌ 忽略 | 超过 GitHub 单文件建议上限，用 `prep_data.py` 从教材重新生成 |
| `outputs/kdd99.db` | 60 MB | ❌ 忽略 | 由 `ch08_sql_practice.py` 自动重建 |
| `data/ch02`、`data/ch05`、`data/ch10` | 12 MB | ✅ | 体量可控，便于读者直接跑 |
| `outputs/*.csv`、`*.png`、`*.html` | 2 MB | ✅ | 运行结果，便于对照；`outputs/index.html` 是一页看完的总览页 |

`data/` 下的 csv 都是 `prep_data.py` 从教材原始文件摊平出来的中间产物，
教材原始 `.xlsx` / `.pbix` 受版权保护，不随仓库分发。

---

## 七、与教材的差异汇总

- **引擎替换**：Power BI 报表 → `pyecharts`；Power BI 图表视觉对象 → `matplotlib`；
  Excel 公式 → `pandas` / `numpy`；MySQL → `sqlite3`（教材语句做了方言适配：
  `datediff` → `julianday`、`DATE_FORMAT` → `strftime`、`LIMIT n,m` → `LIMIT m OFFSET n`）。
- **依赖收敛**：不引入 statsmodels / scikit-learn，K-Means、RFM 分箱、季节分解全部手写，
  只用 pandas + numpy，保证「拷到任何一台装了 pandas 的机器都能跑」。
- **结果对齐**：凡是教材给了参考答案的（RFM、波士顿矩阵、KPI），脚本都会打印比对结果，
  对不上的地方一定会写明原因（见第五节）。
