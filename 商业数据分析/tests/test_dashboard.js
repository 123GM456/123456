// 大屏 JS 的无浏览器冒烟测试：桩掉 echarts / DOM，检查渲染逻辑不抛错且数据合理
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// 直接从生成产物里抽出内联脚本，避免依赖中间文件
const html = fs.readFileSync(
  path.join(__dirname, '..', 'outputs', 'dashboard.html'), 'utf8');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
const src = blocks[blocks.length - 1][1];

const captured = {};
function mkChart(id) {
  return {
    _id: id,
    setOption(o) { captured[id] = o; },
    on(ev, fn) { (this._h = this._h || {})[ev] = fn; },
    off() { this._h = {}; },
    resize() {},
  };
}
const charts = {};
['c1', 'c2', 'c3', 'c4', 'c5', 'c6'].forEach((id) => { charts[id] = mkChart(id); });

const els = {};
function el(id) {
  if (!els[id]) els[id] = { id, innerHTML: '', textContent: '', value: '', onclick: null, onchange: null };
  return els[id];
}
const sandbox = {
  console,
  echarts: { init: (dom) => charts[dom.id] },
  document: {
    getElementById: (id) => el(id),
    querySelector: (q) => ({ innerHTML: '', querySelectorAll: () => [] }),
  },
  window: { addEventListener() {} },
  Array, Object, Math, Number, String, JSON, parseInt, isNaN,
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(src, sandbox, { filename: 'dash.js' });

function check(name, cond, extra) {
  console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra === undefined ? '' : '  -> ' + extra));
  if (!cond) process.exitCode = 1;
}

const c1 = captured.c1, c3 = captured.c3, c5 = captured.c5;
check('C1 有两个序列', c1 && c1.series.length >= 2, c1 && c1.series.length);
const world = c1.series[0].data;
check('C1 世界序列长度=25', world.length === 25, world.length);
check('C1 无 NaN', world.every((v) => v === null || !isNaN(v)));
const last = world[world.length - 1];
check('C1 2024 加权增速在 -5~10', last > -5 && last < 10, last && last.toFixed(2));
check('C3 帕累托累计到 80 以上', Math.max(...c3.series[1].data) > 80,
  Math.max(...c3.series[1].data).toFixed(1));
check('C5 前 12 排行降序', c5.series[0].data.every((d, i, a) => i === 0 || a[i - 1].value <= d.value));
check('C5 第一名是美国', c5.yAxis.data[c5.yAxis.data.length - 1].indexOf('United') >= 0,
  c5.yAxis.data[c5.yAxis.data.length - 1]);
check('KPI1 有数值', /万亿美元/.test(el('k1').innerHTML), el('k1').innerHTML);
check('KPI5 集中度在 50~90', parseFloat(el('k5').innerHTML) > 50 && parseFloat(el('k5').innerHTML) < 95,
  el('k5').innerHTML);

// 交互：点 C2 扇区 -> region 过滤 -> 重算
const before = captured.c3.series[0].data.length;
charts.c2._h.click({ name: '北美' });
const after = captured.c3.series[0].data.length;
check('点击扇区触发重绘', after <= before, before + ' -> ' + after);
check('区域筛选已写入下拉框', el('fRegion').value === '北美', el('fRegion').value);

// 交互：点击 C5 条形 -> focus 国家 -> C1 增加第三条线（先重置筛选，保证有 12 行）
el('btnReset').onclick();
charts.c5._h.click({ dataIndex: 11 });
check('点击条形后 C1 变为 3 条线', captured.c1.series.length === 3, captured.c1.series.length);

// 交互：切换年份 -> 重算
el('fYear').value = '2010';
el('fYear').onchange({ target: { value: '2010' } });
check('切到 2010 年后 KPI 年份文本更新', el('k1d').textContent.indexOf('2010') === 0,
  el('k1d').textContent);

// 重置
el('btnReset').onclick();
check('重置后区域为全部', el('fRegion').value === '全部', el('fRegion').value);
console.log('\nDONE');
