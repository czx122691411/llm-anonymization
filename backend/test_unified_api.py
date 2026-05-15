#!/usr/bin/env python3
"""
测试统一匿名化API
验证策略工厂和API端点是否正常工作
"""

import asyncio
import requests
import json
from typing import Dict, Any


class UnifiedAPITester:
    """统一API测试器"""

    BASE_URL = "http://localhost:8001"

    def __init__(self):
        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json"}

    def test_health_check(self):
        """测试健康检查"""
        print("\n=== 测试健康检查 ===")
        response = self.session.get(f"{self.BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200

    def test_unified_health(self):
        """测试统一API健康检查"""
        print("\n=== 测试统一API健康检查 ===")
        response = self.session.get(f"{self.BASE_URL}/api/unified/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200

    def test_list_methods(self):
        """测试列出所有方法"""
        print("\n=== 测试列出所有方法 ===")
        response = self.session.get(f"{self.BASE_URL}/api/unified/methods")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"支持的方法数量: {len(data.get('methods', []))}")
        for method in data.get('methods', []):
            print(f"\n  - {method['name']} ({method['method']})")
            print(f"    默认配置: {json.dumps(method['default_config'], indent=4, ensure_ascii=False)}")
        return response.status_code == 200

    def test_list_attributes(self):
        """测试列出所有属性"""
        print("\n=== 测试列出所有属性 ===")
        response = self.session.get(f"{self.BASE_URL}/api/unified/attributes")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"支持的属性数量: {len(data.get('attributes', []))}")
        for attr, info in data.get('attributes', {}).items():
            print(f"\n  - {info['label']} ({attr})")
            print(f"    {info['description']}")
        return response.status_code == 200

    def test_anonymize_sync(self, text: str, method: str = "trace_rps_v2"):
        """测试同步匿名化"""
        print(f"\n=== 测试同步匿名化 ({method}) ===")
        print(f"输入文本: {text[:100]}...")

        request_data = {
            "text": text,
            "method": method,
            "config": {
                "target_attributes": ["income"],
                "max_iterations": 2,  # 减少迭代次数以加快测试
                "certainty_threshold": 2
            },
            "options": {
                "enable_progress_stream": False,
                "enable_quality_metrics": True,
                "enable_inference_test": True
            }
        }

        print(f"请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")

        try:
            response = self.session.post(
                f"{self.BASE_URL}/api/unified/anonymize/sync",
                json=request_data,
                headers=self.headers,
                timeout=60  # 60秒超时
            )

            print(f"\n状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"\n任务ID: {data['task_id']}")
                print(f"状态: {data['status']}")
                print(f"方法: {data['method']}")

                if data.get('result'):
                    result = data['result']
                    print(f"\n原文: {result['original_text'][:100]}...")
                    print(f"\n匿名化后: {result['anonymized_text'][:100]}...")
                    print(f"\n修改数量: {len(result.get('changes', []))}")
                    print(f"\n质量分数:")
                    scores = result['quality_scores']
                    print(f"  - 隐私保护: {scores['privacy_protection']}%")
                    print(f"  - 效用保持: {scores['utility_preservation']}%")
                    print(f"  - 文本质量: {scores['text_quality']}%")
                    print(f"  - 推理阻止: {scores['inference_blocking']}%")

                    if result.get('trace_rps_details'):
                        details = result['trace_rps_details']
                        print(f"\nTRACE-RPS 详情:")
                        print(f"  - 迭代次数: {details['iterations']}")
                        print(f"  - 最终置信度: {details['final_certainty']}")
                        print(f"  - 推理链数量: {len(details['reasoning_chains'])}")

                return True
            else:
                print(f"错误响应: {response.text}")
                return False

        except requests.exceptions.Timeout:
            print("请求超时（60秒）")
            return False
        except Exception as e:
            print(f"请求异常: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("开始测试统一匿名化API")
        print("=" * 60)

        results = []

        # 基础测试
        results.append(("健康检查", self.test_health_check()))
        results.append(("统一API健康检查", self.test_unified_health()))
        results.append(("列出方法", self.test_list_methods()))
        results.append(("列出属性", self.test_list_attributes()))

        # 功能测试 - 测试文本
        test_text = """
I am a 31-year-old software engineer living in Zurich, Switzerland.
I work at a tech startup and earn about 120k CHF per year.
I graduated from Stanford University with a CS degree.
        """.strip()

        # 测试三种方法
        results.append(("TRACE-RPS v2 同步", self.test_anonymize_sync(test_text, "trace_rps_v2")))
        results.append(("同构对抗 同步", self.test_anonymize_sync(test_text, "homogeneous")))
        results.append(("异构对抗 同步", self.test_anonymize_sync(test_text, "heterogeneous")))

        # 打印测试结果摘要
        print("\n" + "=" * 60)
        print("测试结果摘要")
        print("=" * 60)

        passed = 0
        failed = 0

        for test_name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name:30s} {status}")
            if result:
                passed += 1
            else:
                failed += 1

        print("=" * 60)
        print(f"总计: {passed} 通过, {failed} 失败")
        print("=" * 60)

        return failed == 0


if __name__ == "__main__":
    tester = UnifiedAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
