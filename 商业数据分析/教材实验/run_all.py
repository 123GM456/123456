"""一键跑完教材实验的全部脚本。

用法：
    py -3.13 run_all.py            # 跑全部步骤
    py -3.13 run_all.py 1 3        # 只跑第 1、3 步
    py -3.13 run_all.py --prep     # 强制重新从教材 xlsx 抽数（需要 openpyxl）
    py -3.13 run_all.py --skip-prep  # 跳过抽数（data/ 已就绪时）

说明：`data/ch01/trans.csv`（65 MB）没有入库，所以全新克隆的仓库第一次运行
需要带 `--prep`，并且解释器要装 openpyxl；之后 `data/` 就绪，默认跳过抽数。

每一步都用同一个解释器（sys.executable）以子进程方式运行，
这样某个脚本失败不会影响其余脚本的日志顺序，也便于单独重跑。
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "scripts")

# (步骤名, 脚本, 说明)
STEPS = [
    ("prep", "prep_data.py", "把教材 xlsx / GBK csv 摊平成 UTF-8 csv"),
    ("ch01", "ch01_data_model.py", "第 1 章 数据模型（星型模型 + 汇总）"),
    ("ch02a", "ch02_excel2pandas.py", "第 2 章 Excel 公式 → pandas"),
    ("ch02b", "ch02_six_methods.py", "第 2 章 六类分析方法 + 四范式"),
    ("ch02c", "ch02_dashboard.py", "第 2 章 pyecharts 看板"),
    ("ch05", "ch05_bank_kpi.py", "第 5 章 银行销售 KPI 看板"),
    ("ch08", "ch08_sql_practice.py", "第 8 章 SQL 实践（sqlite3）"),
    ("ch09", "ch09_user_profile.py", "第 9 章 用户画像（as-of 连接）"),
    ("ch10", "ch10_decompose.py", "第 10 章 效应分解与预报"),
    ("index", "build_index.py", "生成 outputs/index.html 结果总览页"),
]


def run(script: str) -> bool:
    path = os.path.join(SCRIPTS, script)
    if not os.path.exists(path):
        print(f"  ! 缺少脚本 {script}")
        return False
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    print(f"\n===== {script} =====")
    proc = subprocess.run([sys.executable, path], cwd=ROOT, env=env)
    if proc.returncode != 0:
        print(f"  ! {script} 退出码 {proc.returncode}")
        return False
    return True


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force_prep = "--prep" in sys.argv[1:]
    skip_prep = "--skip-prep" in sys.argv[1:]
    if not force_prep:
        # 抽数脚本要读 xlsx，只有 openpyxl 可用时才需要跑；data/ 已就绪就直接跳过
        has_trans = os.path.exists(
            os.path.join(ROOT, "data", "ch01", "trans.csv"))
        skip_prep = skip_prep or has_trans
    wanted = set(args)

    todo = []
    for i, (key, script, desc) in enumerate(STEPS, start=1):
        if key == "prep" and skip_prep:
            continue
        if wanted and str(i) not in wanted and key not in wanted:
            continue
        todo.append((i, key, script, desc))

    if not todo:
        print("没有要执行的步骤。")
        return 0

    print(f"解释器：{sys.executable}")
    print(f"工作目录：{ROOT}")
    failed = []
    for i, key, script, desc in todo:
        print(f"\n[{i}/{len(STEPS)}] {desc}")
        if not run(script):
            failed.append(script)

    print("\n" + "=" * 60)
    if failed:
        print("失败：" + "、".join(failed))
        return 1
    print(f"全部完成（{len(todo)} 步），产物见 outputs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
