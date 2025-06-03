#!/usr/bin/env python3
"""
GitHub Actions工作流验证脚本
验证工作流文件的语法和逻辑
"""
import os
import yaml
import re
from pathlib import Path

def validate_yaml_syntax(file_path):
    """验证YAML语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f"✅ {file_path} - YAML语法正确")
        return True
    except yaml.YAMLError as e:
        print(f"❌ {file_path} - YAML语法错误: {e}")
        return False
    except Exception as e:
        print(f"❌ {file_path} - 文件读取错误: {e}")
        return False

def validate_workflow_structure(file_path):
    """验证工作流结构"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)
        
        # 检查必需的顶级字段
        required_fields = ['name', 'on', 'jobs']
        for field in required_fields:
            if field not in workflow:
                print(f"❌ 缺少必需字段: {field}")
                return False
        
        # 检查jobs结构
        if 'build' not in workflow['jobs']:
            print("❌ 缺少build job")
            return False
        
        build_job = workflow['jobs']['build']
        if 'steps' not in build_job:
            print("❌ build job缺少steps")
            return False
        
        print("✅ 工作流结构正确")
        return True
        
    except Exception as e:
        print(f"❌ 工作流结构验证失败: {e}")
        return False

def check_secrets_usage(file_path):
    """检查secrets使用是否正确"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查条件表达式中的secrets使用
        # 正确: secrets.SECRET_NAME
        # 错误: secrets.SECRET_NAME != ''
        
        # 查找所有if条件
        if_patterns = re.findall(r'if:\s*(.+)', content)
        
        issues = []
        for pattern in if_patterns:
            # 检查是否有错误的secrets比较
            if "secrets." in pattern and "!=" in pattern:
                issues.append(f"可能的错误secrets用法: {pattern.strip()}")
        
        if issues:
            print("⚠️ 发现可能的secrets使用问题:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ secrets使用正确")
            return True
            
    except Exception as e:
        print(f"❌ secrets检查失败: {e}")
        return False

def validate_docker_steps(file_path):
    """验证Docker相关步骤"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow['jobs']['build']['steps']
        step_names = [step.get('name', '') for step in steps]
        
        # 检查必需的Docker步骤
        required_steps = [
            'Checkout repository',
            'Set up Docker Buildx',
            'Build and push Docker image'
        ]
        
        missing_steps = []
        for required_step in required_steps:
            if not any(required_step in name for name in step_names):
                missing_steps.append(required_step)
        
        if missing_steps:
            print(f"❌ 缺少必需的步骤: {missing_steps}")
            return False
        
        print("✅ Docker步骤完整")
        return True
        
    except Exception as e:
        print(f"❌ Docker步骤验证失败: {e}")
        return False

def main():
    """主函数"""
    print("GitHub Actions工作流验证")
    print("=" * 40)
    
    workflow_file = '.github/workflows/docker-build.yml'
    
    if not os.path.exists(workflow_file):
        print(f"❌ 工作流文件不存在: {workflow_file}")
        return False
    
    print(f"验证文件: {workflow_file}")
    print()
    
    # 运行所有验证
    validations = [
        ("YAML语法", lambda: validate_yaml_syntax(workflow_file)),
        ("工作流结构", lambda: validate_workflow_structure(workflow_file)),
        ("Secrets使用", lambda: check_secrets_usage(workflow_file)),
        ("Docker步骤", lambda: validate_docker_steps(workflow_file))
    ]
    
    results = []
    for name, validator in validations:
        print(f"检查 {name}...")
        result = validator()
        results.append(result)
        print()
    
    # 总结
    print("=" * 40)
    print("验证总结")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有验证通过！工作流应该可以正常运行。")
        return True
    else:
        print("⚠️ 存在问题，请检查上述错误。")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
