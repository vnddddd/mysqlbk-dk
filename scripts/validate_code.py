#!/usr/bin/env python3
"""
代码验证脚本
检查Python代码的语法和基本功能
"""
import os
import sys
import ast
import importlib.util

def validate_python_file(file_path):
    """验证Python文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 检查语法
        ast.parse(source)
        print(f"✓ {file_path} - 语法正确")
        return True
    except SyntaxError as e:
        print(f"✗ {file_path} - 语法错误: {e}")
        return False
    except Exception as e:
        print(f"✗ {file_path} - 验证失败: {e}")
        return False

def validate_import(file_path, module_name):
    """验证模块导入"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✓ {module_name} - 导入成功")
        return True
    except ImportError as e:
        print(f"⚠ {module_name} - 导入警告 (缺少依赖): {e}")
        return True  # 缺少依赖是正常的
    except Exception as e:
        print(f"✗ {module_name} - 导入失败: {e}")
        return False

def main():
    """主函数"""
    print("开始验证代码...")
    
    # 要验证的文件
    files_to_validate = [
        ('src/database_parser.py', 'database_parser'),
        ('src/backup_manager.py', 'backup_manager'),
        ('src/b2_uploader.py', 'b2_uploader'),
        ('src/scheduler.py', 'scheduler'),
        ('src/health_check.py', 'health_check'),
        ('src/main.py', 'main'),
        ('scripts/test_system.py', 'test_system'),
    ]
    
    syntax_results = []
    import_results = []
    
    # 验证语法
    print("\n=== 语法验证 ===")
    for file_path, module_name in files_to_validate:
        if os.path.exists(file_path):
            result = validate_python_file(file_path)
            syntax_results.append(result)
        else:
            print(f"✗ {file_path} - 文件不存在")
            syntax_results.append(False)
    
    # 验证导入（仅验证语法正确的文件）
    print("\n=== 导入验证 ===")
    for i, (file_path, module_name) in enumerate(files_to_validate):
        if syntax_results[i] and os.path.exists(file_path):
            result = validate_import(file_path, module_name)
            import_results.append(result)
        else:
            import_results.append(False)
    
    # 统计结果
    print("\n=== 验证结果 ===")
    syntax_passed = sum(syntax_results)
    import_passed = sum(import_results)
    total_files = len(files_to_validate)
    
    print(f"语法验证: {syntax_passed}/{total_files} 通过")
    print(f"导入验证: {import_passed}/{total_files} 通过")
    
    if syntax_passed == total_files:
        print("✓ 所有文件语法正确")
    else:
        print("✗ 存在语法错误")
    
    # 验证配置文件
    print("\n=== 配置文件验证 ===")
    config_files = [
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'docker-compose.dev.yml',
        '.env.example'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✓ {config_file} - 存在")
        else:
            print(f"✗ {config_file} - 不存在")
    
    print("\n验证完成!")

if __name__ == "__main__":
    main()
