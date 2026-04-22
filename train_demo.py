import os
import sys
import json
import time
from datetime import datetime

os.environ['DASHSCOPE_API_KEY'] = 'sk-e68f64387d7c40fa86002e8bb861456e'
os.environ['DEEPSEEK_API_KEY'] = 'sk-30d59ec09f5c495db4271f9c321938cb'

from src.models.providers.registry import get_registry
from src.evaluation import QualityEvaluator

print('='*80)
print('🚀 增强版异构对抗训练 - 实时演示 (10条样本)')
print('='*80)
print('开始时间:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# 配置
MAX_SAMPLES = 10

# 加载数据
print()
print('📂 加载数据...')
with open('data/base_inferences/synthetic/inference_0.jsonl', 'r') as f:
    samples = [json.loads(line.strip()) for line in f]

print('✓ 加载了', len(samples), '条数据，将处理前', MAX_SAMPLES, '条')

# 创建模型
print()
print('🤖 创建模型...')
registry = get_registry(region='china')
quality_model = registry.create_model_instance('deepseek-chat', 0.0)
quality_evaluator = QualityEvaluator(quality_model)
print('✓ 模型已创建')

# 处理数据
results = []
start_time = time.time()

for i, sample in enumerate(samples[:MAX_SAMPLES]):
    username = sample.get('username', 'unknown')
    
    # 提取文本
    comments = sample.get('comments', [])
    if not comments or not comments[0]:
        continue
    
    original_text = comments[0]['comments'][0].get('text', '')
    if len(original_text) < 50:
        continue
    
    print()
    print('📝 处理样本 [%d/%d]: %s' % (i+1, MAX_SAMPLES, username))
    print('   原始文本:', original_text[:80] + '...')
    
    # 简化演示：直接使用第一个评论作为匿名化版本
    if len(comments[0]['comments']) > 1:
        anonymized_text = comments[0]['comments'][1].get('text', original_text)
    else:
        anonymized_text = original_text.replace('covid', 'pandemic')
    
    # 质量评估
    print('   📊 质量评估中...')
    quality_scores = quality_evaluator.evaluate_quality(original_text, anonymized_text)
    
    # 模拟隐私和效用评分
    privacy_score = 0.8
    utility_score = quality_scores.get_utility_score()
    
    print('   ✓ 隐私: %.2f | 效用: %.2f' % (privacy_score, utility_score))
    print('   ✓ 可读性: %.1f/10 | 含义: %.1f/10 | BLEU: %.4f' % (
        quality_scores.readability_score,
        quality_scores.meaning_score,
        quality_scores.bleu
    ))
    
    results.append({
        'username': username,
        'privacy': privacy_score,
        'utility': utility_score,
        'quality': quality_scores.to_dict()
    })
    
    # 进度
    elapsed = time.time() - start_time
    speed = (i + 1) / elapsed * 60 if elapsed > 0 else 0
    eta = (MAX_SAMPLES - i - 1) / speed if speed > 0 else 0
    print('   ⏱  已用: %.1f秒 | 速度: %.1f样本/分 | 预计剩余: %.1f秒' % (elapsed, speed, eta))

# 汇总
print()
print('='*80)
print('📊 训练完成!')
print('='*80)
print('处理样本数:', len(results))
print('总耗时: %.1f秒' % (time.time() - start_time))

# 统计
if results:
    avg_privacy = sum(r['privacy'] for r in results) / len(results)
    avg_utility = sum(r['utility'] for r in results) / len(results)
    avg_readability = sum(r['quality']['readability_score'] for r in results) / len(results)
    avg_meaning = sum(r['quality']['meaning_score'] for r in results) / len(results)
    avg_bleu = sum(r['quality']['bleu'] for r in results) / len(results)
    
    print()
    print('平均评分:')
    print('  隐私: %.3f' % avg_privacy)
    print('  效用: %.3f' % avg_utility)
    print('  可读性: %.2f/10' % avg_readability)
    print('  含义保留: %.2f/10' % avg_meaning)
    print('  BLEU: %.4f' % avg_bleu)

print()
print('='*80)
print('✅ 演示完成！')
print('完整525条训练请运行: python3 train_enhanced.py')
print('='*80)
