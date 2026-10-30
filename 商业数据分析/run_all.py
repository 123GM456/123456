# -*- coding: utf-8 -*-
"""
run_all.py — 一键复现全部结果
=============================
为什么要这个脚本：评分要求"代码可复现"。按顺序跑 7 个脚本即可从原始 CSV
得到清洗数据、模型结论、22 张交互图、1 个大屏、8 张论文配图、1 篇论文、1 个索引页。

用法：
    python run_all.py           # 全流程
    python run_all.py 1 2       # 只跑第 1、2 步
    python run_all.py --py 3=C:\\Python313\\python.exe   # 手动指定第 3 步的解释器

为什么还要「挑解释器」：本机可能装了多个 Python，而 pandas、pyecharts、Pillow、
python-docx 不一定装在同一个解释器里。脚本会按每步的依赖自动挑一个能 import 的解释器，
挑不到就明确报错，而不是让子进程抛一个难懂的 ModuleNotFoundError。

依赖：pandas / numpy / pyecharts / Pillow / python-docx
注意：03、05、06 需要中文字体（Windows 自带微软雅黑即可）。
"""
import glob
import os
import shutil
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))

# 每一步依赖的第三方模块（用于挑选解释器）
STEPS = [
    ("01_load_clean.py", "读取原始 WDI 数据 → 清洗 → data/clean/*.csv", ["pandas", "numpy"]),
    ("02_models.py", "6 个商业分析模型 → outputs/models/*.csv + conclusions.json",
     ["pandas", "numpy"]),
    ("03_visuals.py", "22 张交互图表 → outputs/figs/*.html", ["pandas", "pyecharts"]),
    ("04_dashboard.py", "联动数据大屏 → outputs/dashboard.html", ["pandas", "pyecharts"]),
    ("05_static_charts.py", "8 张论文静态配图（150dpi）→ outputs/figs_png/*.png",
     ["pandas", "PIL"]),
    ("06_report.py", "生成课程论文 → 期末大论文_基于世界银行开放数据的全球宏观经济分析.docx",
     ["docx", "PIL"]),
    ("07_index.py", "生成图表索引页 → outputs/index.html", []),
]


def _candidates():
    """候选解释器：当前解释器优先，再按 PATH 与 Windows 常见安装位置探测。"""
    out = [sys.executable]
    for name in ("python", "python3"):
        p = shutil.which(name)
        if p:
            out.append(p)
    home = os.path.expanduser("~")
    pats = [
        os.path.join(home, "AppData", "Local", "Programs", "Python", "Python3*", "python.exe"),
        os.path.join(home, ".dsh", "dsh-runtimes", "*", "dependencies", "python", "python.exe"),
        r"C:\Python3*\python.exe",
        "/usr/bin/python3*",
    ]
    for pat in pats:
        out.extend(sorted(glob.glob(pat)))
    seen, uniq = set(), []
    for p in out:
        key = os.path.normcase(os.path.abspath(p)) if os.path.exists(p) else p
        if key not in seen and os.path.exists(p):
            seen.add(key)
            uniq.append(p)
    return uniq


_CACHE = {}


def can_import(exe, modules):
    key = (exe, tuple(modules))
    if key in _CACHE:
        return _CACHE[key]
    code = "import " + ", ".join(modules) if modules else "pass"
    try:
        # 注意：某些受限环境里管道（capture_output/capture_output=True）会抛
        # PermissionError，因此这里只丢弃输出、不建管道。
        r = subprocess.run([exe, "-c", code],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=120)
        ok = r.returncode == 0
    except Exception:
        ok = False
    _CACHE[key] = ok
    return ok


def pick_python(modules, manual=None):
    if manual:
        return manual if can_import(manual, modules) else None
    for exe in _candidates():
        if can_import(exe, modules):
            return exe
    return None


def main():
    args = sys.argv[1:]
    picked = [int(a) for a in args if a.isdigit()]
    manual = {}
    for j, a in enumerate(args):
        # 支持 --py 3=C:\Python313\python.exe
        if a == "--py" and j + 1 < len(args):
            k, _, v = args[j + 1].partition("=")
            if k.isdigit() and v:
                manual[int(k)] = v

    print("=" * 70)
    print("全球宏观经济分析 · 一键复现")
    print("=" * 70)
    t0 = time.time()
    for i, (script, desc, mods) in enumerate(STEPS, start=1):
        if picked and i not in picked:
            print(f"[{i}/{len(STEPS)}] 跳过 {script}")
            continue
        exe = pick_python(mods, manual.get(i))
        if exe is None:
            need = "、".join(mods) or "（无）"
            print(f"!! 找不到可 import [{need}] 的 Python 解释器，无法运行 {script}。")
            print("   请先 pip install -r requirements.txt，或用 --py {i}=<解释器路径> 指定。")
            sys.exit(2)
        print(f"\n[{i}/{len(STEPS)}] {script} —— {desc}")
        print(f"    解释器：{exe}")
        t = time.time()
        r = subprocess.run([exe, os.path.join(BASE, "scripts", script)],
                           cwd=BASE, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode != 0:
            print(f"!! {script} 失败（returncode={r.returncode}），已停止。")
            sys.exit(r.returncode)
        print(f"    完成，用时 {time.time() - t:.1f}s")
    print(f"\n全部完成，总用时 {time.time() - t0:.1f}s")
    print("交互大屏：outputs/dashboard.html")
    print("图表索引：outputs/index.html")


if __name__ == "__main__":
    main()
