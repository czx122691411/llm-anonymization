import os, sys
os.environ["DASHSCOPE_API_KEY"] = "sk-e68f64387d7c40fa86002e8bb861456e"
os.environ["DEEPSEEK_API_KEY"] = "sk-30d59ec09f5c495db4271f9c321938cb"
sys.path.insert(0, '/root/llm-anonymization')

print("测试1: 导入registry...")
from src.models.providers.registry import get_registry
print("✓ Registry导入成功")

print("\n测试2: 创建注册表...")
registry = get_registry(region="china")
print("✓ 注册表创建成功")

print("\n测试3: 检查可用提供商...")
available = registry.get_available_providers()
for pid, avail in available.items():
    status_symbol = "✓" if avail.status.value == "available" else "✗"
    print(f"  {status_symbol} {pid}: {avail.status.value}")

print("\n测试4: 创建模型实例...")
defender = registry.create_model_instance("qwen-plus", temperature=0.1)
if defender:
    print("✓ Defender模型创建成功")
    print(f"  模型类型: {type(defender).__name__}")
else:
    print("✗ Defender模型创建失败")

print("\n测试5: 测试预测...")
if defender:
    result = defender.predict_string("你好，请回复'测试成功'")
    print(f"✓ 预测结果: {result[:100]}")
