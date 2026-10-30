# -*- coding: utf-8 -*-
"""
04_dashboard.py — 交互式数据大屏
================================
完全离线：仅引用本地 assets/echarts.min.js，无任何 CDN / 外部请求。

联动设计（1 个状态对象驱动全部组件）：
  状态：{year, region, cluster, income, focus}
  控制器（5 个）：年份下拉 / 区域下拉 / 群体下拉 / 收入分组下拉 / 重置按钮
  被联动组件（8 个）：
    K1-K4 KPI 卡 / C1 全球与中国增速趋势 / C2 区域份额环形图 /
    C3 帕累托曲线 / C4 波士顿矩阵散点 / C5 GDP 排行条形图 /
    C6 聚类群体规模柱 / T1 明细表
  反向联动：点击 C2 的扇区 → 设置 region；点击 C5 的条形 → 设置 focus 国家，
  再由 focus 反写 KPI 卡与 T1 明细表；点击 C6 的柱子 → 设置 cluster。

输出：outputs/dashboard.html
"""
import json
import os

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "clean")
MOD = os.path.join(BASE, "outputs", "models")
OUT = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)

REGION_CN = {
    "North America": "北美",
    "East Asia & Pacific": "东亚与太平洋",
    "Europe & Central Asia": "欧洲与中亚",
    "Latin America & Caribbean": "拉美与加勒比",
    "Middle East & North Africa": "中东与北非",
    "South Asia": "南亚",
    "Sub-Saharan Africa": "撒哈拉以南非洲",
}
INC_CN = {"High income": "高收入", "Upper middle income": "中高收入",
          "Lower middle income": "中低收入", "Low income": "低收入"}


def build_payload():
    cy = pd.read_csv(os.path.join(CLEAN, "country_year.csv"), encoding="utf-8-sig")
    cl = pd.read_csv(os.path.join(MOD, "m4_clusters.csv"), encoding="utf-8-sig")
    cl_map = dict(zip(cl["country_name"], cl["群体"]))
    years = sorted(int(y) for y in cy["year"].unique())
    yidx = {y: i for i, y in enumerate(years)}

    out = []
    for code, g in cy.groupby("country_code"):
        g = g.set_index("year")
        name = str(g["country_name"].iloc[0])
        gdp = [None] * len(years)
        gr = [None] * len(years)
        trade = [None] * len(years)
        unemp = [None] * len(years)
        pgdp = [None] * len(years)
        for y in years:
            if y not in g.index:
                continue
            row = g.loc[y]
            i = yidx[y]
            if pd.notna(row.get("GDP现价")):
                gdp[i] = round(float(row["GDP现价"]) / 1e9, 2)      # 十亿美元
            if pd.notna(row.get("GDP增长率")):
                gr[i] = round(float(row["GDP增长率"]), 2)
            if pd.notna(row.get("贸易占GDP比重")):
                trade[i] = round(float(row["贸易占GDP比重"]), 1)
            if pd.notna(row.get("失业率")):
                unemp[i] = round(float(row["失业率"]), 1)
            if pd.notna(row.get("人均GDP")):
                pgdp[i] = round(float(row["人均GDP"]), 0)
        g0 = g.iloc[0]
        out.append({
            "code": code, "name": name,
            "region": REGION_CN.get(str(g0["region"]), str(g0["region"])),
            "income": INC_CN.get(str(g0["income_group"]), str(g0["income_group"])),
            "cluster": cl_map.get(name, "—"),
            "gdp": gdp, "gr": gr, "trade": trade, "unemp": unemp, "pgdp": pgdp,
        })
    out.sort(key=lambda d: -max([x for x in d["gdp"] if x] or [0]))
    return {"years": years, "countries": out,
            "regions": ["全部"] + sorted({c["region"] for c in out}),
            "clusters": ["全部"] + sorted({c["cluster"] for c in out}),
            "incomes": ["全部"] + ["高收入", "中高收入", "中低收入", "低收入"]}


HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>全球宏观经济数据大屏 · 世界银行 WDI</title>
<script src="../assets/echarts.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a1622;color:#dbe6f0;font-family:"Microsoft YaHei","Segoe UI",sans-serif}
.header{display:flex;align-items:center;justify-content:space-between;padding:14px 22px 8px}
.header h1{font-size:22px;letter-spacing:3px;color:#5B9BD5;font-weight:600}
.header .sub{font-size:12px;color:#7d94ab;margin-top:4px}
.badge{font-size:11px;color:#8fb8e0;border:1px solid #2b4b6b;border-radius:12px;padding:4px 12px}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;
  padding:8px 22px 12px;border-bottom:1px solid #17293b}
.bar label{font-size:12px;color:#7d94ab}
select{background:#12293f;color:#dbe6f0;border:1px solid #2b4b6b;border-radius:4px;
  padding:5px 10px;font-size:13px;cursor:pointer;outline:none}
button{background:#1b3a5a;color:#cfe2f3;border:1px solid #2b4b6b;border-radius:4px;
  padding:5px 14px;font-size:13px;cursor:pointer}
button:hover{background:#24486e}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:12px 22px 4px}
.kpi{background:linear-gradient(135deg,#0f2233,#16334d);border:1px solid #1e3a55;
  border-radius:8px;padding:12px 14px;position:relative;overflow:hidden}
.kpi:after{content:'';position:absolute;left:0;top:0;width:3px;height:100%;background:#5B9BD5}
.kpi .v{font-size:24px;font-weight:700;color:#5B9BD5;line-height:1.2}
.kpi .v small{font-size:12px;color:#7d94ab;font-weight:400;margin-left:3px}
.kpi .l{font-size:12px;color:#8aa4bb;margin-top:5px}
.kpi .d{font-size:11px;color:#6d8aa3;margin-top:3px}
.grid{display:grid;grid-template-columns:1.05fr 1fr 1fr;gap:10px;padding:10px 22px}
.box{background:#0f2233;border:1px solid #1e3a55;border-radius:8px;padding:6px 8px 2px}
.box h3{font-size:12.5px;color:#8aa4bb;font-weight:400;padding:5px 6px 0}
.box h3 b{color:#5B9BD5;font-weight:600}
.plot{width:100%;height:250px}
.plot.tall{height:270px}
.wide{grid-column:1/3}
.full{grid-column:1/4}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#16334d;color:#8aa4bb;padding:6px 4px;font-weight:400;position:sticky;top:0}
td{padding:5px 4px;text-align:center;border-bottom:1px solid #16293b;color:#c6d6e5}
tr:hover td{background:#17324a;cursor:pointer}
.scroll{max-height:250px;overflow-y:auto}
.scroll::-webkit-scrollbar{width:6px}
.scroll::-webkit-scrollbar-thumb{background:#24486e;border-radius:3px}
.footer{text-align:center;font-size:11px;color:#5a7187;padding:10px 0 16px}
.hint{font-size:11px;color:#6d8aa3;margin-left:auto}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>全球宏观经济数据大屏</h1>
    <div class="sub">世界银行 WDI 开放数据 · 2000–2024 · 217 个国家 · 全流程 Python 生成（ECharts 离线渲染）</div>
  </div>
  <div class="badge">数据来源：World Bank WDI（官方下载，非爬虫）</div>
</div>

<div class="bar">
  <label>年份</label><select id="fYear"></select>
  <label>区域</label><select id="fRegion"></select>
  <label>K-Means 群体</label><select id="fCluster"></select>
  <label>收入分组</label><select id="fIncome"></select>
  <button id="btnReset">重置筛选</button>
  <span class="hint">提示：点击环形图扇区 / 排行条形 / 群体柱状图，可直接下钻筛选</span>
</div>

<div class="kpis">
  <div class="kpi"><div class="v" id="k1">--</div><div class="l">筛选范围 GDP 总量</div><div class="d" id="k1d">万亿美元</div></div>
  <div class="kpi"><div class="v" id="k2">--</div><div class="l">筛选范围加权增速</div><div class="d" id="k2d">以上年 GDP 为权重</div></div>
  <div class="kpi"><div class="v" id="k3">--</div><div class="l">第一经济体</div><div class="d" id="k3d">占筛选范围比重</div></div>
  <div class="kpi"><div class="v" id="k4">--</div><div class="l">中国 GDP 份额</div><div class="d" id="k4d">全球占比</div></div>
  <div class="kpi"><div class="v" id="k5">--</div><div class="l">前 10 国集中度</div><div class="d" id="k5d">CR10</div></div>
</div>

<div class="grid">
  <div class="box"><h3>C1 <b>全球与中国增速趋势</b>（%）</h3><div class="plot" id="c1"></div></div>
  <div class="box"><h3>C2 <b>区域 GDP 份额</b>（点击扇区下钻）</h3><div class="plot" id="c2"></div></div>
  <div class="box"><h3>C3 <b>帕累托：累计集中度</b>（%）</h3><div class="plot" id="c3"></div></div>

  <div class="box"><h3>C4 <b>波士顿矩阵</b>（份额 × 增速，气泡=GDP）</h3><div class="plot" id="c4"></div></div>
  <div class="box"><h3>C5 <b>GDP 排行前 12</b>（十亿美元，点击条形下钻）</h3><div class="plot" id="c5"></div></div>
  <div class="box"><h3>C6 <b>K-Means 群体规模</b>（国家数，点击柱子筛选）</h3><div class="plot" id="c6"></div></div>

  <div class="box full"><h3>T1 <b>国家明细</b>（点击行可固定/取消关注）</h3>
    <div class="scroll"><table id="tbl">
      <thead><tr><th>排名</th><th>国家</th><th>地区</th><th>收入分组</th><th>K-Means 群体</th>
      <th>GDP(十亿美元)</th><th>全球份额(%)</th><th>增速(%)</th><th>人均GDP($)</th><th>贸易占比(%)</th><th>失业率(%)</th></tr></thead>
      <tbody></tbody></table></div>
  </div>
</div>
<div class="footer">《商业数据分析》课程大作业 · 基于世界银行开放数据的全球宏观经济分析 · 数据获取/清洗/建模/可视化全流程 Python 实现</div>

<script>
var DATA = __DATA__;
var YEARS = DATA.years, CS = DATA.countries;
var state = { year: YEARS[YEARS.length - 1], region: '全部', cluster: '全部',
              income: '全部', focus: null };

/* ---------- 初始化筛选器 ---------- */
function fill(sel, arr, cur) {
  sel.innerHTML = arr.map(function (v) {
    return '<option value="' + v + '"' + (v === cur ? ' selected' : '') + '>' + v + '</option>';
  }).join('');
}
fill(document.getElementById('fYear'), YEARS.slice().reverse(), state.year);
fill(document.getElementById('fRegion'), DATA.regions, state.region);
fill(document.getElementById('fCluster'), DATA.clusters, state.cluster);
fill(document.getElementById('fIncome'), DATA.incomes, state.income);

/* ---------- 工具 ---------- */
function yIdx(y) { return YEARS.indexOf(y); }
function pass(c) {
  return (state.region === '全部' || c.region === state.region)
      && (state.cluster === '全部' || c.cluster === state.cluster)
      && (state.income === '全部' || c.income === state.income);
}
function sum(a) { var s = 0; for (var i = 0; i < a.length; i++) s += (a[i] || 0); return s; }
function fmt(n, d) { return (n === null || isNaN(n)) ? '--' : n.toFixed(d === undefined ? 1 : d); }

/* 某一年的有效样本（通过筛选且有 GDP 值） */
function snapshot() {
  var i = yIdx(state.year), rows = [];
  CS.forEach(function (c) {
    if (!pass(c)) return;
    var g = c.gdp[i];
    if (g === null || g === undefined) return;
    rows.push({ code: c.code, name: c.name, region: c.region, income: c.income,
                cluster: c.cluster, gdp: g, gr: c.gr[i], share: 0,
                pgdp: c.pgdp[i], trade: c.trade[i], unemp: c.unemp[i] });
  });
  rows.sort(function (a, b) { return b.gdp - a.gdp; });
  var tot = sum(rows.map(function (r) { return r.gdp; }));
  rows.forEach(function (r) { r.share = tot ? r.gdp / tot * 100 : 0; });
  return { rows: rows, total: tot };
}

/* 加权增速：权重取上一年 GDP，避免当年结构变化干扰 */
function weightedGrowth(list, year) {
  var i = yIdx(year), num = 0, den = 0;
  list.forEach(function (c) {
    var g1 = c.gdp[i - 1], r = c.gr[i];
    if (i > 0 && g1 > 0 && r !== null && r !== undefined) { num += g1 * r; den += g1; }
  });
  return den ? num / den : null;
}

/* ---------- 图表实例 ---------- */
var charts = {};
['c1', 'c2', 'c3', 'c4', 'c5', 'c6'].forEach(function (id) {
  charts[id] = echarts.init(document.getElementById(id), null, { renderer: 'canvas' });
});
var AX = { axisLine: { lineStyle: { color: '#2b4b6b' } },
           axisLabel: { color: '#8aa4bb', fontSize: 10 },
           splitLine: { lineStyle: { color: '#16293b' } } };
var BASE = { backgroundColor: 'transparent',
             textStyle: { color: '#8aa4bb' },
             grid: { left: 46, right: 18, top: 30, bottom: 26 },
             tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,34,51,.94)',
                        borderColor: '#2b4b6b', textStyle: { color: '#dbe6f0', fontSize: 11 } } };
var PALETTE = ['#5B9BD5', '#ED7D31', '#70AD47', '#FFC000', '#7030A0',
               '#A5A5A5', '#2E75B6', '#C55A11'];

/* ---------- C1 趋势 ---------- */
function drawC1() {
  var world = [], cn = [], fr = [];
  YEARS.forEach(function (y) {
    var list = CS.filter(function (c) { return pass(c); });
    world.push(weightedGrowth(list, y));
    var c = CS.filter(function (c) { return c.code === 'CHN'; })[0];
    cn.push(c ? c.gr[yIdx(y)] : null);
    if (state.focus) {
      var f = CS.filter(function (c) { return c.code === state.focus; })[0];
      fr.push(f ? f.gr[yIdx(y)] : null);
    }
  });
  var series = [
    { name: '全球（筛选范围加权）', type: 'line', smooth: true, data: world,
      symbolSize: 4, lineStyle: { width: 2.4, color: PALETTE[0] },
      itemStyle: { color: PALETTE[0] }, areaStyle: { opacity: 0.12 } },
    { name: '中国', type: 'line', smooth: true, data: cn, symbolSize: 4,
      lineStyle: { width: 2.4, color: PALETTE[1] }, itemStyle: { color: PALETTE[1] } }
  ];
  if (state.focus) {
    var nm = (CS.filter(function (c) { return c.code === state.focus; })[0] || {}).name;
    series.push({ name: nm, type: 'line', smooth: true, data: fr, symbolSize: 4,
                  lineStyle: { width: 2, type: 'dashed', color: PALETTE[2] },
                  itemStyle: { color: PALETTE[2] } });
  }
  charts.c1.setOption(Object.assign({}, BASE, {
    legend: { top: 2, textStyle: { color: '#8aa4bb', fontSize: 10 }, itemWidth: 12, itemHeight: 8 },
    xAxis: Object.assign({ type: 'category', data: YEARS, boundaryGap: false }, AX),
    yAxis: Object.assign({ type: 'value', name: '%', nameTextStyle: { color: '#8aa4bb', fontSize: 10 } }, AX),
    series: series
  }), true);
}

/* ---------- C2 区域份额 ---------- */
function drawC2(snap) {
  var m = {};
  snap.rows.forEach(function (r) { m[r.region] = (m[r.region] || 0) + r.gdp; });
  var data = Object.keys(m).map(function (k) {
    return { name: k, value: +(m[k] / snap.total * 100).toFixed(2) };
  }).sort(function (a, b) { return b.value - a.value; });
  charts.c2.setOption(Object.assign({}, BASE, {
    tooltip: Object.assign({}, BASE.tooltip, {
      trigger: 'item', formatter: '{b}<br/>份额 {c}%（点击下钻）' }),
    legend: { bottom: 0, textStyle: { color: '#8aa4bb', fontSize: 10 }, itemWidth: 10, itemHeight: 7 },
    series: [{
      type: 'pie', radius: ['38%', '62%'], center: ['50%', '46%'], roseType: 'radius',
      data: data, color: PALETTE,
      itemStyle: { borderColor: '#0f2233', borderWidth: 1 },
      label: { color: '#8aa4bb', fontSize: 9, formatter: '{b}\n{d}%' },
      labelLine: { length: 6, length2: 6 },
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(91,155,213,.6)' } }
    }]
  }), true);
  charts.c2.off('click');
  charts.c2.on('click', function (p) {
    state.region = (state.region === p.name) ? '全部' : p.name;
    syncSelectors(); render();
  });
}

/* ---------- C3 帕累托 ---------- */
function drawC3(snap) {
  var top = snap.rows.slice(0, 24);
  var names = top.map(function (r) { return r.name.length > 9 ? r.name.slice(0, 8) + '…' : r.name; });
  var cum = [], acc = 0;
  top.forEach(function (r) { acc += r.share; cum.push(+acc.toFixed(2)); });
  charts.c3.setOption(Object.assign({}, BASE, {
    tooltip: Object.assign({}, BASE.tooltip, { axisPointer: { type: 'cross' } }),
    legend: { top: 2, textStyle: { color: '#8aa4bb', fontSize: 10 }, itemWidth: 12, itemHeight: 8 },
    xAxis: Object.assign({ type: 'category', data: names,
      axisLabel: { color: '#8aa4bb', fontSize: 9, rotate: 40 } }, AX),
    yAxis: [
      Object.assign({ type: 'value', name: '份额%', max: 40 }, AX),
      Object.assign({ type: 'value', name: '累计%', max: 100 }, AX)
    ],
    series: [
      { name: '个体份额', type: 'bar', data: top.map(function (r) { return +r.share.toFixed(2); }),
        itemStyle: { color: PALETTE[0] }, barMaxWidth: 14 },
      { name: '累计份额', type: 'line', yAxisIndex: 1, smooth: true, symbolSize: 4,
        data: cum, itemStyle: { color: PALETTE[1] }, lineStyle: { width: 2.2, color: PALETTE[1] },
        markLine: { silent: true, symbol: 'none',
          data: [{ yAxis: 80, lineStyle: { color: PALETTE[4], type: 'dashed' },
                   label: { formatter: '80%', color: PALETTE[4], fontSize: 10 } }] } }
    ]
  }), true);
}

/* ---------- C4 波士顿 ---------- */
function drawC4(snap) {
  var rows = snap.rows.filter(function (r) {
    return r.gr !== null && r.gr !== undefined && r.share > 0;
  });
  var yThr = weightedGrowth(CS.filter(pass), state.year) || 0;
  var sh = rows.map(function (r) { return r.share; }).slice().sort(function (a, b) { return a - b; });
  var xThr = sh.length ? sh[Math.floor(sh.length / 2)] : 0;
  var groups = {};
  rows.forEach(function (r) {
    var q = (r.share >= xThr ? '高份额' : '低份额') + '·' + (r.gr >= yThr ? '高增速' : '低增速');
    (groups[q] = groups[q] || []).push([+Math.log10(Math.max(r.share, 0.01)).toFixed(3), r.gr,
                                        r.gdp, r.name]);
  });
  var keys = Object.keys(groups);
  charts.c4.setOption(Object.assign({}, BASE, {
    tooltip: Object.assign({}, BASE.tooltip, {
      trigger: 'item',
      formatter: function (p) {
        return p.value[3] + '<br/>份额 ' + Math.pow(10, p.value[0]).toFixed(2) + '%<br/>增速 ' +
               p.value[1] + '%<br/>GDP ' + p.value[2].toFixed(0) + ' 十亿美元';
      }
    }),
    legend: { top: 2, textStyle: { color: '#8aa4bb', fontSize: 9 }, itemWidth: 10, itemHeight: 7 },
    xAxis: Object.assign({ type: 'value', name: 'log10(份额%)', nameTextStyle: { color: '#8aa4bb', fontSize: 9 } }, AX),
    yAxis: Object.assign({ type: 'value', name: '增速%', nameTextStyle: { color: '#8aa4bb', fontSize: 9 } }, AX),
    series: keys.map(function (k, i) {
      return { name: k, type: 'scatter', data: groups[k],
               symbolSize: function (v) { return Math.max(5, Math.sqrt(Math.max(v[2], 1)) / 22); },
               itemStyle: { color: PALETTE[i % PALETTE.length], opacity: 0.62 } };
    }).concat([{ type: 'line', silent: true, symbol: 'none', data: [[-2, yThr], [2, yThr]],
                 lineStyle: { color: '#4a6b8a', type: 'dashed', width: 1 }, tooltip: { show: false } }])
  }), true);
}

/* ---------- C5 排行 ---------- */
function drawC5(snap) {
  var top = snap.rows.slice(0, 12).reverse();
  charts.c5.setOption(Object.assign({}, BASE, {
    tooltip: Object.assign({}, BASE.tooltip, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
    grid: { left: 92, right: 46, top: 12, bottom: 22 },
    xAxis: Object.assign({ type: 'value', name: '十亿美元' }, AX),
    yAxis: Object.assign({ type: 'category',
      data: top.map(function (r) { return r.name.length > 12 ? r.name.slice(0, 11) + '…' : r.name; }),
      axisLabel: { color: '#8aa4bb', fontSize: 9 } }, AX),
    series: [{ type: 'bar', data: top.map(function (r) {
        return { value: +r.gdp.toFixed(0),
                 itemStyle: { color: r.code === state.focus ? PALETTE[1] : PALETTE[0] } };
      }), barMaxWidth: 13,
      label: { show: true, position: 'right', color: '#8aa4bb', fontSize: 9,
               formatter: function (p) { return p.value.toLocaleString(); } } }]
  }), true);
  charts.c5.off('click');
  charts.c5.on('click', function (p) {
    var hit = top[top.length - 1 - p.dataIndex];
    if (!hit) return;                       // 筛选后不足 12 行时点击空白不报错
    state.focus = (state.focus === hit.code) ? null : hit.code;
    render();
  });
}

/* ---------- C6 群体规模 ---------- */
function drawC6(snap) {
  var m = {};
  snap.rows.forEach(function (r) { m[r.cluster] = (m[r.cluster] || 0) + 1; });
  var keys = Object.keys(m).sort(function (a, b) { return m[b] - m[a]; });
  charts.c6.setOption(Object.assign({}, BASE, {
    tooltip: Object.assign({}, BASE.tooltip, { trigger: 'axis', axisPointer: { type: 'shadow' } }),
    grid: { left: 44, right: 18, top: 22, bottom: 54 },
    xAxis: Object.assign({ type: 'category', data: keys,
      axisLabel: { color: '#8aa4bb', fontSize: 9, interval: 0, rotate: 26 } }, AX),
    yAxis: Object.assign({ type: 'value', name: '国家数' }, AX),
    series: [{ type: 'bar', barMaxWidth: 26,
      data: keys.map(function (k, i) {
        return { value: m[k],
                 itemStyle: { color: (state.cluster === k) ? PALETTE[1] : PALETTE[i % PALETTE.length],
                              opacity: 0.85 } };
      }),
      label: { show: true, position: 'top', color: '#8aa4bb', fontSize: 10 } }]
  }), true);
  charts.c6.off('click');
  charts.c6.on('click', function (p) {
    state.cluster = (state.cluster === p.name) ? '全部' : p.name;
    syncSelectors(); render();
  });
}

/* ---------- KPI 与表格 ---------- */
function drawKPI(snap) {
  var tot = snap.total / 1000;                      // 万亿美元
  var wg = weightedGrowth(CS.filter(pass), state.year);
  var top1 = snap.rows[0] || {};
  var cn = snap.rows.filter(function (r) { return r.code === 'CHN'; })[0];
  var cr10 = snap.rows.slice(0, 10).reduce(function (s, r) { return s + r.share; }, 0);

  document.getElementById('k1').innerHTML = fmt(tot, 2) + '<small>万亿美元</small>';
  document.getElementById('k1d').textContent = state.year + ' 年 · ' + snap.rows.length + ' 国';
  document.getElementById('k2').innerHTML = fmt(wg, 2) + '<small>%</small>';
  document.getElementById('k2d').textContent = state.region + ' / ' + state.cluster;
  document.getElementById('k3').innerHTML = (top1.name ? top1.name.slice(0, 10) : '--')
      + '<small>' + fmt(top1.share, 1) + '%</small>';
  document.getElementById('k3d').textContent = 'GDP ' + fmt(top1.gdp / 1000, 2) + ' 万亿美元';
  document.getElementById('k4').innerHTML = (cn ? fmt(cn.share, 2) : '--') + '<small>%</small>';
  document.getElementById('k4d').textContent = cn ? ('增速 ' + fmt(cn.gr, 2) + '%') : '当前筛选不含中国';
  document.getElementById('k5').innerHTML = fmt(cr10, 1) + '<small>%</small>';
  document.getElementById('k5d').textContent = '前 10 国累计份额';
}

function drawTable(snap) {
  var rows = snap.rows.slice(0, 40);
  var tb = document.querySelector('#tbl tbody');
  tb.innerHTML = rows.map(function (r, i) {
    return '<tr data-code="' + r.code + '"' +
      (r.code === state.focus ? ' style="background:#1b3a55"' : '') + '>' +
      '<td>' + (i + 1) + '</td><td style="text-align:left;padding-left:8px">' + r.name + '</td>' +
      '<td>' + r.region + '</td><td>' + r.income + '</td><td>' + r.cluster + '</td>' +
      '<td>' + r.gdp.toFixed(1) + '</td><td>' + r.share.toFixed(2) + '</td>' +
      '<td>' + fmt(r.gr, 2) + '</td>' +
      '<td>' + (r.pgdp ? Math.round(r.pgdp).toLocaleString() : '--') + '</td>' +
      '<td>' + fmt(r.trade, 1) + '</td><td>' + fmt(r.unemp, 1) + '</td></tr>';
  }).join('');
  Array.prototype.forEach.call(tb.querySelectorAll('tr'), function (tr) {
    tr.onclick = function () {
      var c = tr.getAttribute('data-code');
      state.focus = (state.focus === c) ? null : c;
      render();
    };
  });
}

/* ---------- 主渲染 ---------- */
function render() {
  var snap = snapshot();
  drawC1(); drawC2(snap); drawC3(snap); drawC4(snap);
  drawC5(snap); drawC6(snap);
  drawKPI(snap); drawTable(snap);
}

function syncSelectors() {
  document.getElementById('fRegion').value = state.region;
  document.getElementById('fCluster').value = state.cluster;
  document.getElementById('fIncome').value = state.income;
  document.getElementById('fYear').value = state.year;
}

document.getElementById('fYear').onchange = function (e) {
  state.year = parseInt(e.target.value); render();
};
document.getElementById('fRegion').onchange = function (e) {
  state.region = e.target.value; render();
};
document.getElementById('fCluster').onchange = function (e) {
  state.cluster = e.target.value; render();
};
document.getElementById('fIncome').onchange = function (e) {
  state.income = e.target.value; render();
};
document.getElementById('btnReset').onclick = function () {
  state.region = '全部'; state.cluster = '全部'; state.income = '全部';
  state.focus = null; syncSelectors(); render();
};
window.addEventListener('resize', function () {
  Object.keys(charts).forEach(function (k) { charts[k].resize(); });
});

render();
</script>
</body>
</html>
"""


def main():
    payload = build_payload()
    html = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False,
                                               separators=(",", ":")))
    path = os.path.join(OUT, "dashboard.html")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("[04] 大屏输出：", path)
    print(f"[04] 国家数 {len(payload['countries'])}，年份 {len(payload['years'])}，"
          f"文件大小 {os.path.getsize(path)/1024:.0f} KB")


if __name__ == "__main__":
    main()
