import glob, re, os, io

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def key(name):
    m = re.match(r"(chart|ch3_|ch4_)(\d+)", name)
    if not m:
        return (99, 0)
    return ({"chart": 0, "ch3_": 1, "ch4_": 2}[m.group(1)], int(m.group(2)))


files = [os.path.basename(f) for f in glob.glob(os.path.join(OUT, "*.html"))]
files.sort(key=key)

BTN = ('<button onclick="location.href=\'{target}\'" style="padding:8px 26px;margin:0 10px;'
       'font-size:14px;cursor:pointer;border:1px solid #5B9BD5;border-radius:6px;'
       'background:#5B9BD5;color:#fff;">{text}</button>')
BTN_DIS = ('<button disabled style="padding:8px 26px;margin:0 10px;font-size:14px;'
           'border:1px solid #d1d5db;border-radius:6px;background:#e5e7eb;color:#9ca3af;">{text}</button>')
BTN_HOME = ('<button onclick="location.href=\'{target}\'" style="padding:8px 26px;margin:0 10px;'
            'font-size:14px;cursor:pointer;border:1px solid #70AD47;border-radius:6px;'
            'background:#70AD47;color:#fff;">{text}</button>')

OLD = re.compile(r'<div id="chart-nav".*?</div>', re.S)

for i, f in enumerate(files):
    path = os.path.join(OUT, f)
    s = open(path, encoding="utf-8").read()
    prev_b = BTN.format(target=files[i - 1], text="← 上一张") if i > 0 else BTN_DIS.format(text="← 上一张")
    next_b = BTN.format(target=files[i + 1], text="下一张 →") if i < len(files) - 1 else BTN_DIS.format(text="下一张 →")
    home_b = BTN_HOME.format(target="../index.html", text="返回主界面")
    nav = ('<div id="chart-nav" style="text-align:center;margin:26px 0;padding-top:16px;'
           'border-top:1px solid #e5e7eb;">' + prev_b + home_b + next_b + "</div>")
    if 'id="chart-nav"' in s:
        s = OLD.sub(nav, s)
    else:
        s = s.replace("</body>", nav + "</body>")
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)

print("已处理 HTML 数:", len(files))
