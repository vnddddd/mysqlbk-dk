#!/usr/bin/env python3
"""
数据库连接解析器独立测试脚本
不依赖外部库，只测试解析功能
"""
import os
import sys
import json
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 只导入解析器，避免依赖问题
try:
    from database_parser import DatabaseConnectionParser
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)


class ParserTester:
    """解析器测试器"""
    
    def __init__(self):
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
    
    def test_single_connections(self):
        """测试单个连接格式"""
        print("\n=== 测试单个连接格式 ===")
        
        # TCP格式
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "testuser:testpass@tcp(localhost:3306)/testdb"
            )
            success = len(connections) == 1 and connections[0]['database'] == 'testdb'
            self.log_test("TCP格式", success, f"解析到 {len(connections)} 个连接")
        except Exception as e:
            self.log_test("TCP格式", False, str(e))
        
        # MySQL URL格式
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://testuser:testpass@localhost:3306/testdb"
            )
            success = len(connections) == 1 and connections[0]['database'] == 'testdb'
            self.log_test("MySQL URL格式", success, f"解析到 {len(connections)} 个连接")
        except Exception as e:
            self.log_test("MySQL URL格式", False, str(e))
        
        # SSL格式
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://testuser:testpass@localhost:3306/testdb?ssl-mode=REQUIRED"
            )
            success = (len(connections) == 1 and 
                      connections[0]['database'] == 'testdb' and 
                      connections[0]['ssl_mode'] == 'REQUIRED')
            self.log_test("SSL格式", success, f"SSL模式: {connections[0].get('ssl_mode') if connections else 'None'}")
        except Exception as e:
            self.log_test("SSL格式", False, str(e))
    
    def test_multi_database_same_server(self):
        """测试同服务器多数据库"""
        print("\n=== 测试同服务器多数据库 ===")
        
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://testuser:testpass@localhost:3306/db1,db2,db3"
            )
            success = len(connections) == 3
            databases = [conn['database'] for conn in connections]
            self.log_test("多数据库格式", success, f"数据库: {databases}")
        except Exception as e:
            self.log_test("多数据库格式", False, str(e))
    
    def test_multi_servers(self):
        """测试多服务器连接"""
        print("\n=== 测试多服务器连接 ===")
        
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://user1:pass1@host1:3306/db1;mysql://user2:pass2@host2:3306/db2"
            )
            success = len(connections) == 2
            hosts = [f"{conn['host']}:{conn['port']}" for conn in connections]
            self.log_test("多服务器格式", success, f"服务器: {hosts}")
        except Exception as e:
            self.log_test("多服务器格式", False, str(e))
    
    def test_json_config(self):
        """测试JSON配置格式"""
        print("\n=== 测试JSON配置格式 ===")
        
        # 简单JSON数组
        try:
            json_config = '''[
                {"name": "Production", "connection": "mysql://testuser:testpass@prod:3306/proddb"},
                {"name": "Staging", "connection": "mysql://testuser:testpass@staging:3306/stagingdb", "enabled": true}
            ]'''
            connections = DatabaseConnectionParser.parse_connections(json_config)
            success = len(connections) == 2
            groups = [conn.get('group_name') for conn in connections]
            self.log_test("JSON数组格式", success, f"组名: {groups}")
        except Exception as e:
            self.log_test("JSON数组格式", False, str(e))
        
        # 带自定义配置的JSON
        try:
            json_config = '''[
                {
                    "name": "Production",
                    "connection": "mysql://prod:pass@prod.db.com:3306/proddb",
                    "schedule": "0 2 * * *",
                    "retention_days": 30,
                    "enabled": true
                }
            ]'''
            connections = DatabaseConnectionParser.parse_connections(json_config)
            success = (len(connections) == 1 and 
                      connections[0].get('custom_schedule') == '0 2 * * *' and
                      connections[0].get('custom_retention_days') == 30)
            self.log_test("JSON自定义配置", success, f"自定义字段数: {len([k for k in connections[0].keys() if k.startswith('custom_')])}")
        except Exception as e:
            self.log_test("JSON自定义配置", False, str(e))
    
    def test_connection_grouping(self):
        """测试连接分组功能"""
        print("\n=== 测试连接分组功能 ===")
        
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://user1:pass1@host1:3306/db1,db2;mysql://user2:pass2@host2:3306/db3"
            )
            groups = DatabaseConnectionParser.get_connection_groups(connections)
            success = len(groups) >= 2
            group_names = list(groups.keys())
            self.log_test("连接分组", success, f"分组: {group_names}")
        except Exception as e:
            self.log_test("连接分组", False, str(e))
    
    def test_connection_filtering(self):
        """测试连接过滤功能"""
        print("\n=== 测试连接过滤功能 ===")
        
        try:
            json_config = '''[
                {"name": "Enabled", "connection": "mysql://user:pass@host1:3306/db1", "enabled": true},
                {"name": "Disabled", "connection": "mysql://user:pass@host2:3306/db2", "enabled": false}
            ]'''
            all_connections = DatabaseConnectionParser.parse_connections(json_config)
            enabled_connections = DatabaseConnectionParser.filter_enabled_connections(all_connections)
            success = len(all_connections) == 2 and len(enabled_connections) == 1
            self.log_test("连接过滤", success, f"总数: {len(all_connections)}, 启用: {len(enabled_connections)}")
        except Exception as e:
            self.log_test("连接过滤", False, str(e))
    
    def test_connection_info(self):
        """测试连接信息显示"""
        print("\n=== 测试连接信息显示 ===")
        
        try:
            connections = DatabaseConnectionParser.parse_connections(
                "mysql://testuser:testpass@localhost:3306/testdb"
            )
            if connections:
                info = DatabaseConnectionParser.get_connection_info(connections[0])
                success = 'testuser@localhost:3306/testdb' in info
                self.log_test("连接信息显示", success, f"信息: {info}")
            else:
                self.log_test("连接信息显示", False, "无连接数据")
        except Exception as e:
            self.log_test("连接信息显示", False, str(e))
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 空字符串
        try:
            DatabaseConnectionParser.parse_connections("")
            self.log_test("空字符串处理", False, "应该抛出异常")
        except ValueError:
            self.log_test("空字符串处理", True, "正确抛出ValueError")
        except Exception as e:
            self.log_test("空字符串处理", False, f"错误的异常类型: {type(e)}")
        
        # 无效JSON
        try:
            DatabaseConnectionParser.parse_connections('{"invalid": json}')
            self.log_test("无效JSON处理", False, "应该抛出异常")
        except ValueError:
            self.log_test("无效JSON处理", True, "正确抛出ValueError")
        except Exception as e:
            self.log_test("无效JSON处理", False, f"错误的异常类型: {type(e)}")
        
        # 无效连接格式
        try:
            DatabaseConnectionParser.parse_connections("invalid_connection_string")
            self.log_test("无效格式处理", False, "应该抛出异常")
        except ValueError:
            self.log_test("无效格式处理", True, "正确抛出ValueError")
        except Exception as e:
            self.log_test("无效格式处理", False, f"错误的异常类型: {type(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("MySQL数据库连接解析器测试")
        print("="*50)
        print(f"测试时间: {datetime.now()}")
        
        self.test_single_connections()
        self.test_multi_database_same_server()
        self.test_multi_servers()
        self.test_json_config()
        self.test_connection_grouping()
        self.test_connection_filtering()
        self.test_connection_info()
        self.test_error_handling()
        
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
        return failed_tests == 0


def main():
    """主函数"""
    tester = ParserTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
