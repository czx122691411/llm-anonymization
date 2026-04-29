#!/usr/bin/env python3
"""
快速检查同构DeepSeek评估进度
"""

import json
import os
from pathlib import Path
from datetime import datetime

def check_progress():
    log_file = Path("/home/rooter/llm-anonymization/homogeneous_evaluation_full.log")
    output_dir = Path("/home/rooter/llm-anonymization/homogeneous_results_qwen")

    print("=" * 80)
    print("同构DeepSeek大规模评估进度检查")
    print("=" * 80)

    # 检查日志文件
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()

        # 查找最新的进度信息
        for line in reversed(lines[-50:]):
            if "进度:" in line and "/" in line:
                parts = line.split("进度:")[1].strip()
                if "/263" in parts:
                    current = parts.split("/")[0]
                    percent = float(current) / 263 * 100
                    print(f"\n当前进度: {current}/263 ({percent:.1f}%)")
                    break

    # 检查最新的checkpoint
    checkpoints = sorted(output_dir.glob("checkpoint_*.json"),
                        key=lambda x: int(x.stem.split('_')[1]) if x.stem.split('_')[1].isdigit() else 0)

    if checkpoints:
        latest = checkpoints[-1]
        count = int(latest.stem.split('_')[1])

        # 只读取新生成的checkpoint（今天的18:20之后）
        import stat
        mtime = latest.stat().st_mtime

        if count <= 20 and mtime > 1713776400:  # 2024-04-22 18:20
            # 读取新的checkpoint数据
            with open(latest, 'r') as f:
                data = json.load(f)

            results = data.get("results", [])
            if results:
                import numpy as np
                privacy = [r.get("privacy_score", 0) for r in results]
                utility = [r.get("utility_score", 0) for r in results]
                success = sum(1 for r in results if r.get("success", False))

                print(f"已评估样本: {len(results)}")
                print(f"隐私分数: {np.mean(privacy):.3f} ± {np.std(privacy):.3f}")
                print(f"效用分数: {np.mean(utility):.3f} ± {np.std(utility):.3f}")
                print(f"成功率: {success}/{len(results)} ({success/len(results)*100:.1f}%)")

    # 检查进程状态
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'reevaluate_homogeneous_with_qwen.py' in line and 'python' in line:
                print("\n✓ 评估进程正在运行")
                break
        else:
            print("\n✗ 评估进程未运行")
    except:
        pass

    # 检查最终结果
    final_file = output_dir / "evaluation_results.json"
    if final_file.exists():
        with open(final_file, 'r') as f:
            data = json.load(f)

        results = data.get("results", [])
        if results and len(results) >= 263:
            print("\n✓ 评估已完成！")
            return True

    print("\n" + "=" * 80)
    return False

if __name__ == "__main__":
    check_progress()
