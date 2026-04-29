#!/usr/bin/env python3
"""
训练进度监控脚本
定时检查云服务器上的训练进度并生成报告
"""

import subprocess
import time
import re
from datetime import datetime, timedelta
from pathlib import Path


class TrainingMonitor:
    def __init__(self, server="root@8.147.70.110", log_path="/root/llm-anonymization/training_full.log"):
        self.server = server
        self.log_path = log_path
        self.last_sample = 0
        self.start_time = None
        self.check_count = 0

    def ssh_command(self, command):
        """执行SSH命令"""
        try:
            result = subprocess.run(
                ["ssh", self.server, command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        except Exception as e:
            print(f"SSH命令执行失败: {e}")
            return ""

    def check_process_status(self):
        """检查训练进程状态"""
        output = self.ssh_command("ps aux | grep 'python3.*train_enhanced' | grep -v grep")
        return bool(output.strip())

    def get_latest_progress(self):
        """获取最新训练进度"""
        log = self.ssh_command(f"tail -100 {self.log_path}")
        return log

    def parse_progress(self, log_text):
        """解析训练日志获取进度信息"""
        # 查找处理样本的行
        samples = re.findall(r'处理样本 \[(\d+)/525\]', log_text)
        if samples:
            current = int(samples[-1])
        else:
            current = 0

        # 查找质量评分
        quality_scores = re.findall(
            r'可读性: ([\d.]+)/10, 含义: ([\d.]+)/10, BLEU: ([\d.]+)',
            log_text
        )

        # 查找隐私和效用分数
        privacy_utility = re.findall(
            r'隐私: ([\d.]+) \| 效用: ([\d.]+)',
            log_text
        )

        # 查找配置使用情况
        configs = re.findall(r'使用配置: (\w+)', log_text)

        return {
            'current_sample': current,
            'total_samples': 525,
            'quality_scores': quality_scores[-10:] if quality_scores else [],  # 最近10个
            'privacy_utility': privacy_utility[-10:] if privacy_utility else [],
            'configs': configs
        }

    def calculate_statistics(self, progress):
        """计算统计信息"""
        stats = {
            'avg_readability': 0,
            'avg_meaning': 0,
            'avg_bleu': 0,
            'avg_privacy': 0,
            'avg_utility': 0,
            'privacy_success_rate': 0,
            'utility_success_rate': 0
        }

        if progress['quality_scores']:
            readability = [float(s[0]) for s in progress['quality_scores']]
            meaning = [float(s[1]) for s in progress['quality_scores']]
            bleu = [float(s[2]) for s in progress['quality_scores']]

            stats['avg_readability'] = sum(readability) / len(readability)
            stats['avg_meaning'] = sum(meaning) / len(meaning)
            stats['avg_bleu'] = sum(bleu) / len(bleu)

        if progress['privacy_utility']:
            privacy = [float(s[0]) for s in progress['privacy_utility']]
            utility = [float(s[1]) for s in progress['privacy_utility']]

            stats['avg_privacy'] = sum(privacy) / len(privacy)
            stats['avg_utility'] = sum(utility) / len(utility)
            stats['privacy_success_rate'] = sum(1 for p in privacy if p >= 0.8) / len(privacy) * 100
            stats['utility_success_rate'] = sum(1 for u in utility if u >= 0.6) / len(utility) * 100

        return stats

    def estimate_completion(self, current_sample, elapsed_minutes):
        """估算完成时间"""
        if current_sample == 0 or elapsed_minutes == 0:
            return None

        speed = current_sample / elapsed_minutes  # 样本/分钟
        remaining_samples = 525 - current_sample
        eta_minutes = remaining_samples / speed if speed > 0 else 0

        return {
            'speed': speed,
            'eta_minutes': eta_minutes,
            'completion_time': datetime.now() + timedelta(minutes=eta_minutes)
        }

    def print_header(self):
        """打印报告头部"""
        print("\n" + "="*80)
        print(f"{' '*20}🚀 增强版训练进度监控报告")
        print(f"{' '*18}{'='*40}")
        print(f"{' '*20}时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

    def print_progress(self, progress, stats, estimate):
        """打印进度报告"""
        current = progress['current_sample']
        total = progress['total_samples']
        pct = (current / total * 100) if total > 0 else 0

        print(f"\n📊 训练进度:")
        print(f"  已完成: {current}/{total} ({pct:.1f}%)")
        print(f"  剩余: {total - current} 个样本")

        # 进度条
        bar_length = 50
        filled = int(bar_length * current / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"  [{bar}]")

        if estimate:
            print(f"\n⏱  时间估算:")
            print(f"  处理速度: {estimate['speed']:.2f} 样本/分钟")
            print(f"  预计剩余: {estimate['eta_minutes']:.0f} 分钟")
            print(f"  完成时间: {estimate['completion_time'].strftime('%H:%M:%S')}")

        print(f"\n📈 质量统计 (最近样本):")
        print(f"  平均可读性: {stats['avg_readability']:.2f}/10")
        print(f"  平均含义保留: {stats['avg_meaning']:.2f}/10")
        print(f"  平均BLEU: {stats['avg_bleu']:.4f}")
        print(f"  平均隐私: {stats['avg_privacy']:.3f}")
        print(f"  平均效用: {stats['avg_utility']:.3f}")
        print(f"  隐私达标率: {stats['privacy_success_rate']:.1f}% (≥0.8)")
        print(f"  效用达标率: {stats['utility_success_rate']:.1f}% (≥0.6)")

        if progress['configs']:
            config_counts = {}
            for config in progress['configs']:
                config_counts[config] = config_counts.get(config, 0) + 1
            print(f"\n🎯 配置使用:")
            for config, count in config_counts.items():
                print(f"  {config}: {count} 次")

    def check_for_completion(self, log_text):
        """检查是否完成"""
        if "✅ 训练完成" in log_text or "Training completed" in log_text:
            return True
        if "处理样本 [525/525]" in log_text:
            return True
        return False

    def monitor(self, interval_minutes=3):
        """开始监控"""
        print("🔍 开始监控训练进度...")
        print(f"   检查间隔: {interval_minutes} 分钟")
        print(f"   云服务器: {self.server}")
        print(f"   按 Ctrl+C 停止监控\n")

        self.start_time = datetime.now()

        try:
            while True:
                self.check_count += 1
                now = datetime.now()

                # 检查进程状态
                is_running = self.check_process_status()

                if not is_running:
                    log_text = self.get_latest_progress()
                    if self.check_for_completion(log_text):
                        print("\n" + "🎉"*40)
                        print("✅ 训练已完成！")
                        print("🎉"*40)
                        self.show_final_results()
                        break
                    else:
                        print(f"\n⚠️  警告: 训练进程可能已停止")
                        print(f"   最后一次检查: {now.strftime('%H:%M:%S')}")
                else:
                    # 获取进度
                    log_text = self.get_latest_progress()
                    progress = self.parse_progress(log_text)
                    stats = self.calculate_statistics(progress)

                    # 计算时间估算
                    elapsed = (now - self.start_time).total_seconds() / 60
                    estimate = self.estimate_completion(progress['current_sample'], elapsed)

                    # 打印报告
                    self.print_header()
                    print(f"检查 #{self.check_count} | 进程状态: {'运行中 ✅' if is_running else '已停止 ⚠️'}")
                    self.print_progress(progress, stats, estimate)

                print("\n" + "-"*80)
                print(f"下次检查: {(now + timedelta(minutes=interval_minutes)).strftime('%H:%M:%S')}")

                # 等待下次检查
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n⏸️  监控已停止（用户中断）")
            self.show_summary()

    def show_final_results(self):
        """显示最终结果"""
        log_text = self.get_latest_progress()
        print("\n📊 最终训练统计:")
        print("="*80)

        # 查找最终的统计信息
        final_stats = re.search(
            r'平均隐私: ([\d.]+)\s+平均效用: ([\d.]+)',
            log_text
        )
        if final_stats:
            print(f"  平均隐私: {final_stats.group(1)}")
            print(f"  平均效用: {final_stats.group(2)}")

        # 查找结果文件
        result_files = self.ssh_command("ls -lt /root/llm-anonymization/training_results_enhanced/*.json 2>/dev/null | head -5")
        if result_files:
            print(f"\n  结果文件:")
            for line in result_files.split('\n')[:5]:
                if line.strip():
                    parts = line.split()[-1].split('/')
                    print(f"    - {parts[-1]}")

    def show_summary(self):
        """显示摘要"""
        log_text = self.get_latest_progress()
        progress = self.parse_progress(log_text)
        print(f"\n📋 监控摘要:")
        print(f"  总检查次数: {self.check_count}")
        print(f"  已完成样本: {progress['current_sample']}/525")
        print(f"  最后检查: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    import sys

    # 可以通过命令行参数指定检查间隔
    interval = 3  # 默认3分钟
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            pass

    monitor = TrainingMonitor()
    monitor.monitor(interval_minutes=interval)


if __name__ == "__main__":
    main()
