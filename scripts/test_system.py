#!/usr/bin/env python3
"""
MySQL备份系统测试脚本
用于验证系统各个组件的功能
"""
import os
import sys
import time
import requests
import json
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database_parser import DatabaseConnectionParser
from backup_manager import BackupManager
from b2_uploader import B2Uploader


class SystemTester:
    """系统测试器"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test(self, test_name, success, message=""):
        """记录测试结果"""
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_database_parser(self):
        """测试数据库连接解析器"""
        print("\n=== 测试数据库连接解析器 ===")

        # 测试TCP格式
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "testuser:testpass@tcp(localhost:3306)/testdb"
            )
            self.log_test("TCP格式解析", len(connections) == 1, f"解析到 {len(connections)} 个连接")
        except Exception as e:
            self.log_test("TCP格式解析", False, str(e))

        # 测试MySQL URL格式
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://testuser:testpass@localhost:3306/testdb"
            )
            self.log_test("MySQL URL格式解析", len(connections) == 1, f"解析到 {len(connections)} 个连接")
        except Exception as e:
            self.log_test("MySQL URL格式解析", False, str(e))

        # 测试多数据库格式
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://testuser:testpass@localhost:3306/db1,db2,db3"
            )
            self.log_test("多数据库格式解析", len(connections) == 3, f"解析到 {len(connections)} 个连接")
        except Exception as e:
            self.log_test("多数据库格式解析", False, str(e))

        # 测试SSL格式
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://testuser:testpass@localhost:3306/testdb?ssl-mode=REQUIRED"
            )
            success = len(connections) == 1 and connections[0].get('ssl_mode') == 'REQUIRED'
            self.log_test("SSL格式解析", success, f"SSL模式: {connections[0].get('ssl_mode') if connections else 'None'}")
        except Exception as e:
            self.log_test("SSL格式解析", False, str(e))

        # 测试多服务器格式（分号分隔）
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://user1:pass1@host1:3306/db1;mysql://user2:pass2@host2:3306/db2"
            )
            self.log_test("多服务器格式解析", len(connections) == 2, f"解析到 {len(connections)} 个连接")
        except Exception as e:
            self.log_test("多服务器格式解析", False, str(e))

        # 测试JSON格式
        try:
            json_config = '''[
                {"name": "Production", "connection": "mysql://testuser:testpass@prod:3306/proddb"},
                {"name": "Staging", "connection": "mysql://testuser:testpass@staging:3306/stagingdb", "enabled": true}
            ]'''
            connections = DatabaseConnectionParser.parse_connections(json_config)
            self.log_test("JSON格式解析", len(connections) == 2, f"解析到 {len(connections)} 个连接")
        except Exception as e:
            self.log_test("JSON格式解析", False, str(e))

        # 测试连接分组
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://user1:pass1@host1:3306/db1,db2;mysql://user2:pass2@host2:3306/db3"
            )
            groups = DatabaseConnectionParser.get_connection_groups(connections)
            self.log_test("连接分组功能", len(groups) >= 2, f"分组数量: {len(groups)}")
        except Exception as e:
            self.log_test("连接分组功能", False, str(e))
    
    def test_health_endpoints(self):
        """测试健康检查端点"""
        print("\n=== 测试健康检查端点 ===")
        
        endpoints = [
            ("/health", "基本健康检查"),
            ("/status", "详细状态"),
            ("/metrics", "系统指标")
        ]
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code == 200
                message = f"状态码: {response.status_code}"
                if success:
                    data = response.json()
                    if endpoint == "/health":
                        message += f", 状态: {data.get('status', 'unknown')}"
                self.log_test(description, success, message)
            except requests.exceptions.RequestException as e:
                self.log_test(description, False, f"请求失败: {str(e)}")
            except Exception as e:
                self.log_test(description, False, f"解析失败: {str(e)}")
    
    def test_manual_operations(self):
        """测试手动操作"""
        print("\n=== 测试手动操作 ===")
        
        # 测试手动备份
        try:
            response = requests.post(f"{self.base_url}/backup/run", timeout=60)
            success = response.status_code == 200
            message = f"状态码: {response.status_code}"
            if success:
                data = response.json()
                message += f", 消息: {data.get('message', 'No message')}"
            self.log_test("手动备份", success, message)
        except requests.exceptions.RequestException as e:
            self.log_test("手动备份", False, f"请求失败: {str(e)}")
        
        # 等待一段时间再测试清理
        time.sleep(2)
        
        # 测试手动清理
        try:
            response = requests.post(f"{self.base_url}/cleanup/run", timeout=30)
            success = response.status_code == 200
            message = f"状态码: {response.status_code}"
            if success:
                data = response.json()
                message += f", 消息: {data.get('message', 'No message')}"
            self.log_test("手动清理", success, message)
        except requests.exceptions.RequestException as e:
            self.log_test("手动清理", False, f"请求失败: {str(e)}")
    
    def test_service_availability(self):
        """测试服务可用性"""
        print("\n=== 测试服务可用性 ===")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            success = response.status_code == 200
            self.log_test("服务可用性", success, f"服务{'可用' if success else '不可用'}")
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("服务可用性", False, f"连接失败: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始系统测试...")
        print(f"测试时间: {datetime.now()}")
        print(f"目标服务: {self.base_url}")
        
        # 测试数据库解析器（不需要服务运行）
        self.test_database_parser()
        
        # 检查服务是否可用
        if not self.test_service_availability():
            print("\n⚠ 服务不可用，跳过需要服务运行的测试")
            self.print_summary()
            return
        
        # 测试健康检查端点
        self.test_health_endpoints()
        
        # 测试手动操作
        self.test_manual_operations()
        
        # 打印测试摘要
        self.print_summary()
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*50)
        print("测试摘要")
        print("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n测试完成!")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MySQL备份系统测试脚本")
    parser.add_argument("--url", default="http://localhost:8080", 
                       help="服务URL (默认: http://localhost:8080)")
    parser.add_argument("--parser-only", action="store_true",
                       help="只测试数据库解析器")
    
    args = parser.parse_args()
    
    tester = SystemTester(args.url)
    
    if args.parser_only:
        tester.test_database_parser()
        tester.print_summary()
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()
