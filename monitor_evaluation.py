#!/usr/bin/env python3
"""
监控同构DeepSeek评估进度
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta

def monitor_progress():
    output_dir = Path("homogeneous_results_qwen")

    print("=" * 80)
    print("同构DeepSeek评估进度监控")
    print("=" * 80)

    last_count = 0
    start_time = datetime.now()

    while True:
        # 查找最新的checkpoint文件
        checkpoints = sorted(output_dir.glob("checkpoint_*.json"),
                            key=lambda x: int(x.stem.split('_')[1]))

        if checkpoints:
            latest_checkpoint = checkpoints[-1]
            count = int(latest_checkpoint.stem.split('_')[1])

            if count != last_count:
                # 读取最新checkpoint
                with open(latest_checkpoint, 'r') as f:
                    data = json.load(f)

                results = data.get("results", [])
                success_count = sum(1 for r in results if r.get("success", False))

                # 计算统计
                privacy_scores = [r.get("privacy_score", 0) for r in results]
                utility_scores = [r.get("utility_score", 0) for r in results]

                import numpy as np

                # 计算时间
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = count / elapsed if elapsed > 0 else 0
                remaining = (263 - count) / rate if rate > 0 else 0

                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 进度: {count}/263 ({count/263*100:.1f}%)")
                print(f"  成功: {success_count}/{count} ({success_count/count*100:.1f}%)")
                print(f"  隐私: {np.mean(privacy_scores):.3f} ± {np.std(privacy_scores):.3f}")
                print(f"  效用: {np.mean(utility_scores):.3f} ± {np.std(utility_scores):.3f}")
                print(f"  速度: {rate:.2f} 样本/秒")
                print(f"  预计剩余: {remaining/60:.1f} 分钟")

                last_count = count

                # 检查是否完成
                if count >= 263:
                    print("\n✓ 评估完成！")
                    break

        # 检查是否有最终结果文件
        final_file = output_dir / "evaluation_results.json"
        if final_file.exists():
            print("\n✓ 发现最终结果文件，评估完成！")
            break

        # 等待一段时间再检查
        time.sleep(30)  # 每30秒检查一次

    # 读取最终统计
    stats_file = output_dir / "statistics.json"
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            stats = json.load(f)

        print("\n" + "=" * 80)
        print("最终评估统计")
        print("=" * 80)
        print(f"总样本数: {stats['total_samples']}")
        print(f"隐私分数: {stats['privacy']['mean']:.3f} ± {stats['privacy']['std']:.3f}")
        print(f"效用分数: {stats['utility']['mean']:.3f} ± {stats['utility']['std']:.3f}")
        print(f"综合成功率: {stats['success']['rate']:.1f}%")
        print("=" * 80)

if __name__ == "__main__":
    try:
        monitor_progress()
    except KeyboardInterrupt:
        print("\n监控已中断")
